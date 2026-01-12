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

/**
 * Hook for Google Places Autocomplete integration
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
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const listenerRef = useRef<google.maps.MapsEventListener | null>(null);

  // Check if Google Maps is loaded
  useEffect(() => {
    const checkGoogleMaps = () => {
      if (window.google?.maps?.places) {
        setIsLoaded(true);
        setError(null);
        return true;
      }
      return false;
    };

    // Check immediately
    if (checkGoogleMaps()) return;

    // Poll for Google Maps to load
    const interval = setInterval(() => {
      if (checkGoogleMaps()) {
        clearInterval(interval);
      }
    }, 100);

    // Timeout after 10 seconds
    const timeout = setTimeout(() => {
      clearInterval(interval);
      if (!window.google?.maps?.places) {
        console.warn("Google Maps failed to load within 10 seconds");
        setError("Address suggestions unavailable");
      }
    }, 10000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, []);

  // Initialize autocomplete when input and Google Maps are ready
  useEffect(() => {
    if (!isLoaded || !inputRef.current) return;

    // Clean up previous instance
    if (listenerRef.current) {
      google.maps.event.removeListener(listenerRef.current);
    }
    if (autocompleteRef.current) {
      google.maps.event.clearInstanceListeners(autocompleteRef.current);
    }

    try {
      // Create new autocomplete instance
      const autocomplete = new google.maps.places.Autocomplete(inputRef.current, {
        componentRestrictions: { country: countryRestriction },
        types: ["address"],
        fields: ["address_components", "formatted_address", "geometry", "name"],
      });

      // Add place changed listener
      listenerRef.current = autocomplete.addListener("place_changed", () => {
        const result = autocomplete.getPlace();

        if (!result.address_components) {
          console.warn("No address components in place result");
          return;
        }

        const placeResult = parseAddressComponents(result);
        setPlace(placeResult);
        onPlaceSelect?.(placeResult);
      });

      autocompleteRef.current = autocomplete;
    } catch (err) {
      console.error("Failed to initialize Google Places Autocomplete:", err);
      setError("Failed to initialize address search");
    }

    return () => {
      if (listenerRef.current) {
        google.maps.event.removeListener(listenerRef.current);
      }
      if (autocompleteRef.current) {
        google.maps.event.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, [isLoaded, inputRef, onPlaceSelect, countryRestriction]);

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

