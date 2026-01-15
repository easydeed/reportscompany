'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Phone, MapPin, Home, Check, Loader2, 
  ChevronRight, Search, CheckCircle2
} from 'lucide-react';
import { useGooglePlaces, PlaceResult } from '@/hooks/useGooglePlaces';

interface Props {
  agentCode: string;
  themeColor: string;
  agentName: string;
}

type Step = 'phone' | 'address' | 'confirm' | 'processing' | 'success';

interface Property {
  apn: string;
  fips: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  owner_name?: string;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
  year_built?: number;
}

// Progress stages for property search
const SEARCH_STAGES = [
  { id: 'locating', label: 'Locating property...' },
  { id: 'verifying', label: 'Verifying ownership records...' },
  { id: 'fetching', label: 'Fetching property details...' },
];

// Progress stages for report generation
const REPORT_STAGES = [
  { id: 'analyzing', label: 'Analyzing market data...' },
  { id: 'comparables', label: 'Finding comparable homes...' },
  { id: 'generating', label: 'Generating your report...' },
  { id: 'sending', label: 'Sending to your phone...' },
];

export function ConsumerLandingWizard({ agentCode, themeColor, agentName }: Props) {
  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [currentStage, setCurrentStage] = useState(0);
  const [searchStage, setSearchStage] = useState(0);
  
  // Google Places autocomplete - use state for input element to trigger re-renders
  const [inputElement, setInputElement] = useState<HTMLInputElement | null>(null);
  const addressInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);
  
  // Callback ref to track when input mounts/unmounts
  const setAddressInputRef = useCallback((node: HTMLInputElement | null) => {
    addressInputRef.current = node;
    setInputElement(node);
  }, []);
  
  // Handle place selection - search for property
  const handlePlaceSelect = useCallback((place: PlaceResult) => {
    console.log('Place selected:', place);
    setSelectedPlace(place);
    setAddress(place.fullAddress);
  }, []);
  
  const { isLoaded: googleLoaded, error: placesError } = useGooglePlaces(
    addressInputRef,
    { onPlaceSelect: handlePlaceSelect }
  );
  
  // Reinitialize autocomplete when input element changes
  useEffect(() => {
    if (inputElement && googleLoaded && window.google?.maps?.places) {
      console.log('Initializing Google Places autocomplete');
    }
  }, [inputElement, googleLoaded]);
  
  // When a place is selected, auto-trigger search
  useEffect(() => {
    if (selectedPlace && step === 'address') {
      handleAddressSearchFromPlace(selectedPlace);
    }
  }, [selectedPlace]);

  // Format phone as user types
  const formatPhone = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 10);
    if (digits.length >= 6) {
      return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
    } else if (digits.length >= 3) {
      return `(${digits.slice(0,3)}) ${digits.slice(3)}`;
    }
    return digits;
  };

  // Step 1: Phone validation
  const handlePhoneSubmit = () => {
    const digits = phone.replace(/\D/g, '');
    if (digits.length !== 10) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }
    setError('');
    setStep('address');
  };
  
  // Animate through search stages
  useEffect(() => {
    if (!searching) {
      setSearchStage(0);
      return;
    }

    const interval = setInterval(() => {
      setSearchStage((prev) => {
        if (prev < SEARCH_STAGES.length - 1) return prev + 1;
        return prev;
      });
    }, 800);

    return () => clearInterval(interval);
  }, [searching]);

  // Search with Google Places result
  const handleAddressSearchFromPlace = async (place: PlaceResult) => {
    setSearching(true);
    setSearchStage(0);
    setError('');
    
    try {
      const res = await fetch(`/api/proxy/v1/cma/${agentCode}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          address: place.address,
          city: place.city,
          state: place.state
        })
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Search failed');
      }
      
      const data = await res.json();
      setProperties(data);
      
      if (data.length === 0) {
        setError('No properties found. Please check the address and try again.');
      } else if (data.length === 1) {
        // Auto-select if only one result
        setSelectedProperty(data[0]);
        setStep('confirm');
      }
    } catch (err: any) {
      setError(err.message || 'Could not search. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  // Step 2: Address search (manual fallback)
  const handleAddressSearch = async () => {
    if (!address.trim()) {
      setError('Please enter your property address');
      return;
    }
    
    setSearching(true);
    setSearchStage(0);
    setError('');
    
    try {
      const res = await fetch(`/api/proxy/v1/cma/${agentCode}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Search failed');
      }
      
      const data = await res.json();
      setProperties(data);
      
      if (data.length === 0) {
        setError('No properties found. Please check the address and try again.');
      } else if (data.length === 1) {
        // Auto-select if only one result
        setSelectedProperty(data[0]);
        setStep('confirm');
      }
    } catch (err: any) {
      setError(err.message || 'Could not search. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  // Select property from list
  const handleSelectProperty = (property: Property) => {
    setSelectedProperty(property);
    setStep('confirm');
  };

  // Animate through report stages while processing
  useEffect(() => {
    if (step !== 'processing') return;

    const interval = setInterval(() => {
      setCurrentStage((prev) => {
        if (prev < REPORT_STAGES.length - 1) return prev + 1;
        return prev;
      });
    }, 1500);

    return () => clearInterval(interval);
  }, [step]);

  // Step 3: Submit request
  const handleSubmit = async () => {
    if (!consent) {
      setError('Please agree to the terms to continue');
      return;
    }
    
    setStep('processing');
    setCurrentStage(0);
    setError('');
    
    try {
      const res = await fetch(`/api/proxy/v1/cma/${agentCode}/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone.replace(/\D/g, ''),
          property_apn: selectedProperty!.apn,
          property_fips: selectedProperty!.fips,
          property_address: selectedProperty!.address,
          property_city: selectedProperty!.city,
          property_state: selectedProperty!.state,
          property_zip: selectedProperty!.zip,
          consent_given: consent
        })
      });
      
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Request failed');
      }
      
      // Wait for animation to complete, then show success
      setTimeout(() => setStep('success'), 3000);
      
    } catch (err: any) {
      setStep('confirm');
      setError(err.message || 'Something went wrong. Please try again.');
    }
  };

  // Render current step
  return (
    <div className="min-h-[300px]">
      <AnimatePresence mode="wait">
        {/* STEP 1: Phone */}
        {step === 'phone' && (
          <motion.div
            key="phone"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <StepIndicator current={1} total={3} color={themeColor} />
            
            <div className="flex items-center gap-2 mb-4">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <Phone className="w-4 h-4" style={{ color: themeColor }} />
              </div>
              <span className="font-medium text-gray-700">Your Phone Number</span>
            </div>
            
            <Input
              type="tel"
              placeholder="(555) 555-5555"
              value={phone}
              onChange={(e) => setPhone(formatPhone(e.target.value))}
              className="text-lg text-center h-12"
              autoFocus
            />
            
            <p className="text-xs text-gray-500 text-center">
              We&apos;ll text your report to this number
            </p>
            
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            
            <Button 
              onClick={handlePhoneSubmit}
              className="w-full h-12 text-base text-white"
              style={{ backgroundColor: themeColor }}
            >
              Continue <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </motion.div>
        )}

        {/* STEP 2: Address */}
        {step === 'address' && (
          <motion.div
            key="address"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <StepIndicator current={2} total={3} color={themeColor} />
            
            <div className="flex items-center gap-2 mb-4">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <MapPin className="w-4 h-4" style={{ color: themeColor }} />
              </div>
              <span className="font-medium text-gray-700">Your Property Address</span>
            </div>
            
            {/* Show search animation OR input */}
            {searching ? (
              <div className="py-4">
                {/* Animated Loader */}
                <div className="flex justify-center mb-4">
                  <div className="relative">
                    <div 
                      className="w-16 h-16 rounded-full border-4"
                      style={{ borderColor: `${themeColor}30` }}
                    />
                    <div 
                      className="absolute inset-0 w-16 h-16 rounded-full border-4 border-transparent animate-spin"
                      style={{ borderTopColor: themeColor }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Search className="w-5 h-5" style={{ color: themeColor }} />
                    </div>
                  </div>
                </div>
                
                {/* Search Stages */}
                <div className="space-y-2">
                  {SEARCH_STAGES.map((stage, index) => (
                    <motion.div 
                      key={stage.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ 
                        opacity: index <= searchStage ? 1 : 0.3,
                        x: 0 
                      }}
                      transition={{ delay: index * 0.1 }}
                      className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-300 ${
                        index < searchStage 
                          ? 'text-green-600' 
                          : index === searchStage
                          ? ''
                          : 'text-gray-400'
                      }`}
                      style={{ 
                        backgroundColor: index === searchStage ? `${themeColor}15` : 'transparent',
                        color: index === searchStage ? themeColor : undefined
                      }}
                    >
                      <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                        {index < searchStage ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500" />
                        ) : index === searchStage ? (
                          <Loader2 className="w-5 h-5 animate-spin" style={{ color: themeColor }} />
                        ) : (
                          <div className="w-2 h-2 rounded-full bg-current opacity-50" />
                        )}
                      </div>
                      <span className="text-sm font-medium">{stage.label}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
              <>
                <div className="relative">
                  <Input
                    ref={setAddressInputRef}
                    type="text"
                    placeholder="Start typing your address..."
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddressSearch()}
                    className="text-base h-12 pr-12"
                    autoComplete="off"
                    autoFocus
                  />
                  <button
                    onClick={handleAddressSearch}
                    disabled={loading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-gray-100"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                    ) : (
                      <Search className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </div>
                
                <p className="text-xs text-gray-500">
                  {!googleLoaded && !placesError && "Loading address suggestions..."}
                  {googleLoaded && !placesError && "Start typing to see address suggestions"}
                  {placesError && "Enter your full address"}
                </p>
              </>
            )}
            
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            
            {/* Property Results */}
            {!searching && properties.length > 1 && (
              <div className="space-y-2 mt-4">
                <p className="text-sm text-gray-600 font-medium">Select your property:</p>
                {properties.map((prop, i) => (
                  <button
                    key={i}
                    onClick={() => handleSelectProperty(prop)}
                    className="w-full p-3 text-left border rounded-xl hover:border-gray-400 hover:bg-gray-50 transition"
                  >
                    <p className="font-medium text-gray-900">{prop.address}</p>
                    <p className="text-sm text-gray-500">
                      {prop.city}, {prop.state} {prop.zip}
                      {prop.owner_name && ` • ${prop.owner_name}`}
                    </p>
                  </button>
                ))}
              </div>
            )}
            
            {!searching && (
              <button 
                onClick={() => { setStep('phone'); setProperties([]); }}
                className="text-sm text-gray-500 hover:text-gray-700 w-full text-center py-2"
              >
                ← Back
              </button>
            )}
          </motion.div>
        )}

        {/* STEP 3: Confirm */}
        {step === 'confirm' && selectedProperty && (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <StepIndicator current={3} total={3} color={themeColor} />
            
            <div className="flex items-center gap-2 mb-4">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <Home className="w-4 h-4" style={{ color: themeColor }} />
              </div>
              <span className="font-medium text-gray-700">Confirm Your Property</span>
            </div>
            
            {/* Property Card */}
            <div className="bg-gray-50 p-4 rounded-xl border">
              <p className="font-semibold text-gray-900">{selectedProperty.address}</p>
              <p className="text-gray-600 text-sm">
                {selectedProperty.city}, {selectedProperty.state} {selectedProperty.zip}
              </p>
              {selectedProperty.owner_name && (
                <p className="text-gray-500 text-sm mt-1">
                  Owner: {selectedProperty.owner_name}
                </p>
              )}
              {(selectedProperty.bedrooms || selectedProperty.sqft) && (
                <div className="flex gap-3 mt-2 text-sm text-gray-600">
                  {selectedProperty.bedrooms && <span>{selectedProperty.bedrooms} bed</span>}
                  {selectedProperty.bathrooms && <span>{selectedProperty.bathrooms} bath</span>}
                  {selectedProperty.sqft && <span>{selectedProperty.sqft.toLocaleString()} sqft</span>}
                </div>
              )}
            </div>
            
            {/* Consent */}
            <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
              <Checkbox
                checked={consent}
                onCheckedChange={(v) => setConsent(v as boolean)}
                id="consent"
                className="mt-0.5"
              />
              <label htmlFor="consent" className="text-sm text-gray-600 leading-tight cursor-pointer">
                I agree to receive my home value report via text and to be contacted by {agentName} about my property.
              </label>
            </div>
            
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            
            <Button 
              onClick={handleSubmit}
              disabled={!consent}
              className="w-full h-12 text-base text-white"
              style={{ backgroundColor: themeColor, opacity: consent ? 1 : 0.5 }}
            >
              Get My Free Report
            </Button>
            
            <button 
              onClick={() => { setStep('address'); setSelectedProperty(null); }}
              className="text-sm text-gray-500 hover:text-gray-700 w-full text-center py-2"
            >
              ← Change address
            </button>
          </motion.div>
        )}

        {/* PROCESSING - Interactive Progress */}
        {step === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-6"
          >
            {/* Animated Loader */}
            <div className="flex justify-center mb-6">
              <div className="relative">
                {/* Outer ring */}
                <div 
                  className="w-20 h-20 rounded-full border-4"
                  style={{ borderColor: `${themeColor}30` }}
                />
                {/* Spinning ring */}
                <div 
                  className="absolute inset-0 w-20 h-20 rounded-full border-4 border-transparent animate-spin"
                  style={{ borderTopColor: themeColor }}
                />
                {/* Inner icon */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <Home className="w-7 h-7 animate-pulse" style={{ color: themeColor }} />
                </div>
              </div>
            </div>
            
            {/* Progress Stages */}
            <div className="space-y-2">
              {REPORT_STAGES.map((stage, index) => (
                <motion.div 
                  key={stage.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ 
                    opacity: index <= currentStage ? 1 : 0.3,
                    x: 0 
                  }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex items-center gap-3 p-2.5 rounded-lg transition-all duration-300 ${
                    index < currentStage 
                      ? 'text-green-600' 
                      : index === currentStage
                      ? ''
                      : 'text-gray-400'
                  }`}
                  style={{ 
                    backgroundColor: index === currentStage ? `${themeColor}15` : 'transparent',
                    color: index === currentStage ? themeColor : undefined
                  }}
                >
                  <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                    {index < currentStage ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    ) : index === currentStage ? (
                      <Loader2 className="w-5 h-5 animate-spin" style={{ color: themeColor }} />
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-current opacity-50" />
                    )}
                  </div>
                  <span className="text-sm font-medium">{stage.label}</span>
                </motion.div>
              ))}
            </div>
            
            <p className="text-center text-xs text-gray-500 mt-4">
              This usually takes 10-15 seconds
            </p>
          </motion.div>
        )}

        {/* SUCCESS */}
        {step === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-8 text-center"
          >
            <div className="relative inline-block mb-4">
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <Check className="w-8 h-8" style={{ color: themeColor }} />
              </div>
              {/* Celebration ring */}
              <div 
                className="absolute inset-0 w-16 h-16 rounded-full border-2 animate-ping"
                style={{ borderColor: `${themeColor}40` }}
              />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Your Report is on the Way!
            </h3>
            <p className="text-gray-600 mb-4">
              Check your phone for a text message with your personalized home value report.
            </p>
            <div className="bg-gray-50 rounded-xl p-4 text-sm">
              <p className="text-gray-500">Sent to:</p>
              <p className="font-medium text-gray-900">{phone}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


// Step indicator component
function StepIndicator({ current, total, color }: { current: number; total: number; color: string }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 rounded-full transition-all ${
            i + 1 <= current ? 'w-8' : 'w-4'
          }`}
          style={{ 
            backgroundColor: i + 1 <= current ? color : '#E5E7EB'
          }}
        />
      ))}
    </div>
  );
}
