'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Phone, MapPin, Home, Check, Loader2, 
  ChevronRight, Search
} from 'lucide-react';

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

export function ConsumerLandingWizard({ agentCode, themeColor, agentName }: Props) {
  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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

  // Step 2: Address search
  const handleAddressSearch = async () => {
    if (!address.trim()) {
      setError('Please enter your property address');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${apiUrl}/v1/cma/${agentCode}/search`, {
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
      setLoading(false);
    }
  };

  // Select property from list
  const handleSelectProperty = (property: Property) => {
    setSelectedProperty(property);
    setStep('confirm');
  };

  // Step 3: Submit request
  const handleSubmit = async () => {
    if (!consent) {
      setError('Please agree to the terms to continue');
      return;
    }
    
    setStep('processing');
    setError('');
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${apiUrl}/v1/cma/${agentCode}/request`, {
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
      
      // Wait a moment for dramatic effect, then show success
      setTimeout(() => setStep('success'), 1500);
      
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
            
            <div className="relative">
              <Input
                type="text"
                placeholder="Enter your address..."
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddressSearch()}
                className="text-base h-12 pr-12"
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
            
            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}
            
            {/* Property Results */}
            {properties.length > 1 && (
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
            
            <button 
              onClick={() => { setStep('phone'); setProperties([]); }}
              className="text-sm text-gray-500 hover:text-gray-700 w-full text-center py-2"
            >
              ← Back
            </button>
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

        {/* PROCESSING */}
        {step === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-12 text-center"
          >
            <div 
              className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
              style={{ backgroundColor: `${themeColor}20` }}
            >
              <Loader2 
                className="w-8 h-8 animate-spin" 
                style={{ color: themeColor }} 
              />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Generating Your Report...
            </h3>
            <p className="text-gray-600 text-sm">
              Analyzing property data and finding comparables
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
            <div 
              className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
              style={{ backgroundColor: `${themeColor}20` }}
            >
              <Check 
                className="w-8 h-8" 
                style={{ color: themeColor }} 
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

