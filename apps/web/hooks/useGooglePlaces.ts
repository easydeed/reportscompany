"use client";

import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Parsed place result from Google Places Autocomplete
 */
export interface PlaceResult {
  streetNumber: string;
  street: string;
  address: string; // Full street address (number + street)
  city: string;
  state: string;
  zip: string;
  county: string;
  fullAddress: string; // Google's formatted address
  lat?: number;
  lng?: number;
}

interface UseGooglePlacesOptions {
  onPlaceSelect?: (place: PlaceResult) => void;
  countryRestriction?: string;
}

// Track if script is being/has been loaded globally
let scriptLoadPromise: Promise<void> | null = null;

/**
 * Dynamically load Google Maps script if not already loaded
 */
function loadGoogleMapsScript(): Promise<void> {
  // Already loaded
  if (window.google?.maps?.places) {
    return Promise.resolve();
  }

  // Already loading
  if (scriptLoadPromise) {
    return scriptLoadPromise;
  }

  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  if (!apiKey) {
    console.error("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is not configured");
    return Promise.reject(new Error("Google Maps API key not configured"));
  }

  console.log("Loading Google Maps script...");

  // Start loading - use callback instead of loading=async for reliable initialization
  scriptLoadPromise = new Promise((resolve, reject) => {
    // Define callback function that Google will call when ready
    const callbackName = `initGoogleMaps_${Date.now()}`;
    (window as any)[callbackName] = () => {
      console.log("Google Maps callback fired, API ready");
      delete (window as any)[callbackName];
      resolve();
    };

    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&callback=${callbackName}`;
    script.async = true;
    script.defer = true;
    script.onerror = () => {
      console.error("Failed to load Google Maps script");
      delete (window as any)[callbackName];
      reject(new Error("Failed to load Google Maps script"));
    };
    document.head.appendChild(script);
  });

  return scriptLoadPromise;
}

/**
 * Hook for Google Places Autocomplete integration
 * Automatically loads Google Maps script on-demand if not already loaded
 *
 * @param inputRef - Ref to the input element
 * @param options - Configuration options
 * @returns { place, isLoaded, error, reset }
 */
export function useGooglePlaces(
  inputRef: React.RefObject<HTMLInputElement | null>,
  options?: UseGooglePlacesOptions
) {
  const { onPlaceSelect, countryRestriction = "us" } = options || {};

  const [place, setPlace] = useState<PlaceResult | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inputReady, setInputReady] = useState(false);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const listenerRef = useRef<google.maps.MapsEventListener | null>(null);
  const onPlaceSelectRef = useRef(onPlaceSelect);
  
  // Keep callback ref up to date
  useEffect(() => {
    onPlaceSelectRef.current = onPlaceSelect;
  }, [onPlaceSelect]);

  // Load Google Maps script on-demand
  useEffect(() => {
    let cancelled = false;

    const loadMaps = async () => {
      try {
        await loadGoogleMapsScript();
        if (!cancelled && window.google?.maps?.places) {
          setIsLoaded(true);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          console.warn("Google Maps failed to load:", err);
          setError("Address suggestions unavailable");
        }
      }
    };

    // Check if already loaded
    if (window.google?.maps?.places) {
      setIsLoaded(true);
      return;
    }

    loadMaps();

    return () => {
      cancelled = true;
    };
  }, []);
  
  // Poll for input element to be ready (since refs don't trigger re-renders)
  useEffect(() => {
    if (!isLoaded) return;
    
    const checkInput = () => {
      if (inputRef.current) {
        setInputReady(true);
        return true;
      }
      return false;
    };
    
    // Check immediately
    if (checkInput()) return;
    
    // Poll for input
    const interval = setInterval(() => {
      if (checkInput()) {
        clearInterval(interval);
      }
    }, 100);
    
    return () => clearInterval(interval);
  }, [isLoaded, inputRef]);

  // Initialize autocomplete when input and Google Maps are ready
  useEffect(() => {
    if (!isLoaded || !inputReady || !inputRef.current) {
      return;
    }
    
    const input = inputRef.current;
    console.log('Initializing Google Places Autocomplete on input:', input.placeholder);

    // Clean up previous instance
    if (listenerRef.current) {
      google.maps.event.removeListener(listenerRef.current);
      listenerRef.current = null;
    }
    if (autocompleteRef.current) {
      google.maps.event.clearInstanceListeners(autocompleteRef.current);
      autocompleteRef.current = null;
    }

    try {
      // Create new autocomplete instance
      const autocomplete = new google.maps.places.Autocomplete(input, {
        componentRestrictions: { country: countryRestriction },
        types: ["address"],
        fields: ["address_components", "formatted_address", "geometry", "name"],
      });

      // Add place changed listener
      listenerRef.current = autocomplete.addListener("place_changed", () => {
        const result = autocomplete.getPlace();
        console.log('Place changed event:', result);

        if (!result.address_components) {
          console.warn("No address components in place result");
          return;
        }

        const placeResult = parseAddressComponents(result);
        console.log('Parsed place result:', placeResult);
        setPlace(placeResult);
        onPlaceSelectRef.current?.(placeResult);
      });

      autocompleteRef.current = autocomplete;
      console.log('Google Places Autocomplete initialized successfully');
    } catch (err) {
      console.error("Failed to initialize Google Places Autocomplete:", err);
      setError("Failed to initialize address search");
    }

    return () => {
      if (listenerRef.current) {
        google.maps.event.removeListener(listenerRef.current);
        listenerRef.current = null;
      }
      if (autocompleteRef.current) {
        google.maps.event.clearInstanceListeners(autocompleteRef.current);
        autocompleteRef.current = null;
      }
      setInputReady(false);
    };
  }, [isLoaded, inputReady, countryRestriction]);

  const reset = useCallback(() => {
    setPlace(null);
  }, []);

  return { place, isLoaded, error, reset };
}

/**
 * Parse Google Places address components into a structured PlaceResult
 */
function parseAddressComponents(place: google.maps.places.PlaceResult): PlaceResult {
  let streetNumber = "";
  let street = "";
  let city = "";
  let state = "";
  let zip = "";
  let county = "";

  for (const component of place.address_components || []) {
    const type = component.types[0];

    switch (type) {
      case "street_number":
        streetNumber = component.long_name;
        break;
      case "route":
        street = component.long_name;
        break;
      case "locality":
        city = component.long_name;
        break;
      case "sublocality_level_1":
        // Fallback for city if locality not present
        if (!city) city = component.long_name;
        break;
      case "administrative_area_level_1":
        state = component.short_name;
        break;
      case "administrative_area_level_2":
        county = component.long_name.replace(" County", "");
        break;
      case "postal_code":
        zip = component.long_name;
        break;
    }
  }

  const fullStreetAddress = streetNumber ? `${streetNumber} ${street}`.trim() : street;

  return {
    streetNumber,
    street,
    address: fullStreetAddress,
    city,
    state,
    zip,
    county,
    fullAddress: place.formatted_address || "",
    lat: place.geometry?.location?.lat(),
    lng: place.geometry?.location?.lng(),
  };
}

export default useGooglePlaces;

