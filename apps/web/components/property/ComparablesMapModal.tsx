"use client";

import { useCallback, useState, useMemo } from "react";
import {
  GoogleMap,
  useJsApiLoader,
  Marker,
  InfoWindow,
} from "@react-google-maps/api";
import { X, Home, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Comparable } from "@/lib/wizard-types";

interface SubjectProperty {
  lat: number;
  lng: number;
  address: string;
  bedrooms?: number | null;
  bathrooms?: number | null;
  sqft?: number | null;
}

interface ComparablesMapModalProps {
  isOpen: boolean;
  onClose: () => void;
  subjectProperty: SubjectProperty;
  comparables: Comparable[];
  selectedIds: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  maxSelections?: number;
}

const containerStyle = {
  width: "100%",
  height: "100%",
};

const libraries: ("places")[] = ["places"];

export function ComparablesMapModal({
  isOpen,
  onClose,
  subjectProperty,
  comparables,
  selectedIds,
  onSelectionChange,
  maxSelections = 8,
}: ComparablesMapModalProps) {
  const [activeMarker, setActiveMarker] = useState<string | null>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
    libraries,
  });

  const center = useMemo(
    () => ({
      lat: subjectProperty.lat,
      lng: subjectProperty.lng,
    }),
    [subjectProperty.lat, subjectProperty.lng]
  );

  const onLoad = useCallback(
    (map: google.maps.Map) => {
      setMap(map);

      // Fit bounds to include all markers
      const bounds = new google.maps.LatLngBounds();
      bounds.extend({ lat: subjectProperty.lat, lng: subjectProperty.lng });
      comparables.forEach((comp) => {
        if (comp.lat && comp.lng) {
          bounds.extend({ lat: comp.lat, lng: comp.lng });
        }
      });
      map.fitBounds(bounds);

      // Don't zoom in too much
      const listener = google.maps.event.addListener(map, "idle", () => {
        if (map.getZoom()! > 16) map.setZoom(16);
        google.maps.event.removeListener(listener);
      });
    },
    [subjectProperty, comparables]
  );

  const handleMarkerClick = (compId: string) => {
    const isSelected = selectedIds.includes(compId);

    if (isSelected) {
      // Deselect
      onSelectionChange(selectedIds.filter((id) => id !== compId));
    } else {
      // Select (if under max)
      if (selectedIds.length < maxSelections) {
        onSelectionChange([...selectedIds, compId]);
      }
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  // Custom marker icons using SVG paths
  const getSubjectIcon = (): google.maps.Symbol | undefined => {
    if (!google.maps?.SymbolPath) return undefined;
    return {
      path: google.maps.SymbolPath.CIRCLE,
      fillColor: "#2563eb",
      fillOpacity: 1,
      strokeColor: "#1d4ed8",
      strokeWeight: 3,
      scale: 14,
    };
  };

  const getSelectedIcon = (): google.maps.Symbol | undefined => {
    if (!google.maps?.SymbolPath) return undefined;
    return {
      path: google.maps.SymbolPath.CIRCLE,
      fillColor: "#22c55e",
      fillOpacity: 1,
      strokeColor: "#16a34a",
      strokeWeight: 2,
      scale: 11,
    };
  };

  const getAvailableIcon = (): google.maps.Symbol | undefined => {
    if (!google.maps?.SymbolPath) return undefined;
    return {
      path: google.maps.SymbolPath.CIRCLE,
      fillColor: "#f97316",
      fillOpacity: 1,
      strokeColor: "#ea580c",
      strokeWeight: 2,
      scale: 11,
    };
  };

  if (!isOpen) return null;

  if (loadError) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-background p-6 rounded-lg shadow-xl max-w-md">
          <p className="text-destructive font-medium mb-2">Error loading Google Maps</p>
          <p className="text-sm text-muted-foreground mb-4">
            Please check that the Google Maps API key is configured correctly.
          </p>
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </div>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-background p-6 rounded-lg shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <p>Loading map...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-xl w-full max-w-6xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-muted/30">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <MapPin className="w-5 h-5 text-primary" />
              Select Comparables on Map
            </h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              Click markers to select/deselect properties. Selected:{" "}
              <span className="font-medium text-foreground">
                {selectedIds.length}/{maxSelections}
              </span>
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          <GoogleMap
            mapContainerStyle={containerStyle}
            center={center}
            zoom={14}
            onLoad={onLoad}
            options={{
              streetViewControl: false,
              mapTypeControl: true,
              fullscreenControl: false,
              zoomControl: true,
              styles: [
                {
                  featureType: "poi",
                  elementType: "labels",
                  stylers: [{ visibility: "off" }],
                },
              ],
            }}
          >
            {/* Subject Property Marker */}
            <Marker
              position={{ lat: subjectProperty.lat, lng: subjectProperty.lng }}
              icon={getSubjectIcon()}
              title="Subject Property"
              onClick={() => setActiveMarker("subject")}
              zIndex={1000}
            />

            {activeMarker === "subject" && (
              <InfoWindow
                position={{ lat: subjectProperty.lat, lng: subjectProperty.lng }}
                onCloseClick={() => setActiveMarker(null)}
              >
                <div className="p-2 min-w-[220px]">
                  <div className="bg-primary text-primary-foreground text-xs px-2 py-1 rounded mb-2 inline-flex items-center gap-1">
                    <Home className="w-3 h-3" />
                    SUBJECT PROPERTY
                  </div>
                  <p className="font-semibold text-sm">{subjectProperty.address}</p>
                  <div className="flex gap-3 text-xs text-gray-600 mt-2">
                    {subjectProperty.bedrooms && <span>🛏 {subjectProperty.bedrooms}</span>}
                    {subjectProperty.bathrooms && <span>🛁 {subjectProperty.bathrooms}</span>}
                    {subjectProperty.sqft && <span>📐 {subjectProperty.sqft.toLocaleString()} sqft</span>}
                  </div>
                </div>
              </InfoWindow>
            )}

            {/* Comparable Markers */}
            {comparables.map((comp) => {
              if (!comp.lat || !comp.lng) return null;
              const isSelected = selectedIds.includes(comp.id);

              return (
                <Marker
                  key={comp.id}
                  position={{ lat: comp.lat, lng: comp.lng }}
                  icon={isSelected ? getSelectedIcon() : getAvailableIcon()}
                  title={comp.address}
                  onClick={() => handleMarkerClick(comp.id)}
                  onMouseOver={() => setActiveMarker(comp.id)}
                  onMouseOut={() => {
                    // Only clear if not clicking
                    setTimeout(() => {
                      setActiveMarker((current) =>
                        current === comp.id ? null : current
                      );
                    }, 100);
                  }}
                  zIndex={isSelected ? 999 : 100}
                />
              );
            })}

            {/* InfoWindow for Comparables */}
            {activeMarker && activeMarker !== "subject" && (() => {
              const comp = comparables.find((c) => c.id === activeMarker);
              if (!comp || comp.lat === undefined || comp.lng === undefined) return null;
              const isSelected = selectedIds.includes(comp.id);

              return (
                <InfoWindow
                  position={{ lat: comp.lat, lng: comp.lng }}
                  onCloseClick={() => setActiveMarker(null)}
                >
                  <div className="p-2 min-w-[240px] max-w-[300px]">
                    {/* Property Image */}
                    {comp.photo_url ? (
                      <img
                        src={comp.photo_url}
                        alt={comp.address}
                        className="w-full h-28 object-cover rounded-lg mb-2"
                      />
                    ) : (
                      <div className="w-full h-28 bg-gradient-to-br from-muted to-muted/50 rounded-lg mb-2 flex items-center justify-center">
                        <Home className="w-8 h-8 text-muted-foreground/50" />
                      </div>
                    )}

                    {/* Status Badges */}
                    <div className="flex gap-2 mb-2 flex-wrap">
                      <span
                        className={`text-xs px-2 py-1 rounded font-medium ${
                          isSelected
                            ? "bg-green-100 text-green-800"
                            : "bg-orange-100 text-orange-800"
                        }`}
                      >
                        {isSelected ? "✓ SELECTED" : "AVAILABLE"}
                      </span>
                      {comp.status && (
                        <span className="text-xs px-2 py-1 rounded bg-blue-100 text-blue-800">
                          {comp.status}
                        </span>
                      )}
                    </div>

                    {/* Address */}
                    <p className="font-semibold text-sm leading-tight">{comp.address}</p>
                    {comp.city && (
                      <p className="text-xs text-gray-500">{comp.city}</p>
                    )}

                    {/* Price */}
                    <p className="text-lg font-bold text-primary mt-1">
                      {formatPrice(comp.price)}
                    </p>

                    {/* Details */}
                    <div className="flex gap-3 text-xs text-gray-600 mt-2">
                      <span>🛏 {comp.bedrooms}</span>
                      <span>🛁 {comp.bathrooms}</span>
                      <span>📐 {comp.sqft?.toLocaleString()} sqft</span>
                    </div>

                    {/* Distance & Year */}
                    <div className="flex gap-3 text-xs text-gray-500 mt-1">
                      {comp.distance_miles !== undefined && (
                        <span>📍 {comp.distance_miles.toFixed(2)} mi</span>
                      )}
                      {comp.year_built && <span>🏠 Built {comp.year_built}</span>}
                    </div>

                    {/* Click hint */}
                    <button
                      onClick={() => handleMarkerClick(comp.id)}
                      className={`w-full mt-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                        isSelected
                          ? "bg-red-50 text-red-700 hover:bg-red-100"
                          : selectedIds.length >= maxSelections
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-green-50 text-green-700 hover:bg-green-100"
                      }`}
                      disabled={!isSelected && selectedIds.length >= maxSelections}
                    >
                      {isSelected
                        ? "Remove from Selection"
                        : selectedIds.length >= maxSelections
                        ? "Maximum Selections Reached"
                        : "Add to Selection"}
                    </button>
                  </div>
                </InfoWindow>
              );
            })()}
          </GoogleMap>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 bg-background/95 backdrop-blur rounded-lg shadow-lg p-3 border">
            <p className="text-xs font-semibold mb-2">Legend</p>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-xs">
                <span className="w-3.5 h-3.5 rounded-full bg-primary border-2 border-primary/70"></span>
                <span>Subject Property</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-3.5 h-3.5 rounded-full bg-green-500 border-2 border-green-600"></span>
                <span>Selected ({selectedIds.length})</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-3.5 h-3.5 rounded-full bg-orange-500 border-2 border-orange-600"></span>
                <span>Available ({comparables.filter(c => c.lat && c.lng).length - selectedIds.length})</span>
              </div>
            </div>
          </div>

          {/* Selection count badge */}
          <div className="absolute top-4 right-4 bg-background/95 backdrop-blur rounded-lg shadow-lg px-4 py-2 border">
            <span className="text-sm font-medium">
              {selectedIds.length} / {maxSelections} selected
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-muted/30 flex justify-between items-center">
          <div className="text-sm">
            {selectedIds.length < 4 && (
              <span className="text-amber-600 flex items-center gap-1">
                <span className="text-lg">⚠️</span>
                Select at least 4 comparables (currently {selectedIds.length})
              </span>
            )}
            {selectedIds.length >= 4 && selectedIds.length <= maxSelections && (
              <span className="text-green-600 flex items-center gap-1">
                <span className="text-lg">✓</span>
                {selectedIds.length} comparables selected
              </span>
            )}
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => onSelectionChange([])}
              disabled={selectedIds.length === 0}
            >
              Clear All
            </Button>
            <Button onClick={onClose}>
              Done
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ComparablesMapModal;

