"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export interface PlaceResult {
  streetNumber: string;
  street: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  county: string;
  fullAddress: string;
  lat?: number;
  lng?: number;
}

interface UseGooglePlacesOptions {
  onPlaceSelect?: (place: PlaceResult) => void;
}

export function useGooglePlaces(
  inputRef: React.RefObject<HTMLInputElement | null>,
  options?: UseGooglePlacesOptions
) {
  const [place, setPlace] = useState<PlaceResult | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const listenerRef = useRef<google.maps.MapsEventListener | null>(null);

  // Check if Google Maps is loaded
  useEffect(() => {
    const checkGoogleMaps = () => {
      if (window.google?.maps?.places) {
        setIsLoaded(true);
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

    // Cleanup after 10 seconds
    const timeout = setTimeout(() => {
      clearInterval(interval);
      console.warn("Google Maps failed to load within 10 seconds");
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

    // Create new autocomplete instance
    const autocomplete = new google.maps.places.Autocomplete(inputRef.current, {
      componentRestrictions: { country: "us" },
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

      let streetNumber = "";
      let street = "";
      let city = "";
      let state = "";
      let zip = "";
      let county = "";

      for (const component of result.address_components) {
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

      const fullStreetAddress = streetNumber
        ? `${streetNumber} ${street}`.trim()
        : street;

      const placeResult: PlaceResult = {
        streetNumber,
        street,
        address: fullStreetAddress,
        city,
        state,
        zip,
        county,
        fullAddress: result.formatted_address || "",
        lat: result.geometry?.location?.lat(),
        lng: result.geometry?.location?.lng(),
      };

      setPlace(placeResult);
      options?.onPlaceSelect?.(placeResult);
    });

    autocompleteRef.current = autocomplete;

    return () => {
      if (listenerRef.current) {
        google.maps.event.removeListener(listenerRef.current);
      }
      if (autocompleteRef.current) {
        google.maps.event.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, [isLoaded, inputRef, options?.onPlaceSelect]);

  const reset = useCallback(() => {
    setPlace(null);
  }, []);

  return { place, isLoaded, reset };
}

