'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  MapPin, Home, Check, Loader2,
  ChevronRight, Search, CheckCircle2, Phone, Mail,
} from 'lucide-react';
import { useGooglePlaces, PlaceResult } from '@/hooks/useGooglePlaces';

interface Props {
  agentCode: string;
  themeColor: string;
  agentName: string;
  agentPhone: string | null;
  agentEmail: string | null;
  prefillAddress?: string;
}

type Step = 'address' | 'confirm' | 'contact' | 'processing' | 'success';
type DeliveryMethod = 'sms' | 'email';

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

const SEARCH_STAGES = [
  { id: 'locating', label: 'Locating property...' },
  { id: 'verifying', label: 'Verifying records...' },
  { id: 'fetching', label: 'Fetching property details...' },
];

const REPORT_STAGES = [
  { id: 'analyzing', label: 'Analyzing market data...' },
  { id: 'comparables', label: 'Finding comparable homes...' },
  { id: 'generating', label: 'Generating your report...' },
  { id: 'sending', label: 'Delivering your report...' },
];

export function CmaFunnel({
  agentCode, themeColor, agentName, agentPhone, agentEmail, prefillAddress,
}: Props) {
  const [step, setStep] = useState<Step>('address');
  const [address, setAddress] = useState(prefillAddress || '');
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);

  // Contact capture state
  const [deliveryMethod, setDeliveryMethod] = useState<DeliveryMethod>('sms');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [consent, setConsent] = useState(false);

  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [searchStage, setSearchStage] = useState(0);
  const [reportStage, setReportStage] = useState(0);

  // Google Places
  const [inputElement, setInputElement] = useState<HTMLInputElement | null>(null);
  const addressInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedPlace, setSelectedPlace] = useState<PlaceResult | null>(null);

  const setAddressInputRef = useCallback((node: HTMLInputElement | null) => {
    addressInputRef.current = node;
    setInputElement(node);
  }, []);

  const handlePlaceSelect = useCallback((place: PlaceResult) => {
    setSelectedPlace(place);
    setAddress(place.fullAddress);
  }, []);

  const { isLoaded: googleLoaded, error: placesError } = useGooglePlaces(
    addressInputRef,
    { onPlaceSelect: handlePlaceSelect },
  );

  useEffect(() => {
    if (inputElement && googleLoaded && window.google?.maps?.places) {
      // autocomplete binds automatically via hook
    }
  }, [inputElement, googleLoaded]);

  useEffect(() => {
    if (selectedPlace && step === 'address') {
      searchFromPlace(selectedPlace);
    }
  }, [selectedPlace]);

  // Search stage animation
  useEffect(() => {
    if (!searching) { setSearchStage(0); return; }
    const interval = setInterval(() => {
      setSearchStage(prev => (prev < SEARCH_STAGES.length - 1 ? prev + 1 : prev));
    }, 800);
    return () => clearInterval(interval);
  }, [searching]);

  // Report stage animation
  useEffect(() => {
    if (step !== 'processing') return;
    const interval = setInterval(() => {
      setReportStage(prev => (prev < REPORT_STAGES.length - 1 ? prev + 1 : prev));
    }, 1500);
    return () => clearInterval(interval);
  }, [step]);

  // ------- Handlers -------

  const formatPhone = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 10);
    if (digits.length >= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    if (digits.length >= 3) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
    return digits;
  };

  const searchFromPlace = async (place: PlaceResult) => {
    setSearching(true);
    setSearchStage(0);
    setError('');
    try {
      const res = await fetch(`/api/proxy/v1/cma/${agentCode}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address: place.address, city: place.city, state: place.state }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || 'Search failed');
      }
      const data = await res.json();
      handleSearchResults(data);
    } catch (err: any) {
      setError(err.message || 'Could not search. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const handleManualSearch = async () => {
    if (!address.trim()) { setError('Please enter your property address'); return; }
    setSearching(true);
    setSearchStage(0);
    setError('');
    try {
      const res = await fetch(`/api/proxy/v1/cma/${agentCode}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || 'Search failed');
      }
      handleSearchResults(await res.json());
    } catch (err: any) {
      setError(err.message || 'Could not search. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const handleSearchResults = (data: Property[]) => {
    setProperties(data);
    if (data.length === 0) {
      setError('No properties found. Please check the address and try again.');
    } else if (data.length === 1) {
      setSelectedProperty(data[0]);
      setStep('confirm');
    }
  };

  const handleConfirm = () => {
    setError('');
    setStep('contact');
  };

  const handleSubmit = async () => {
    if (deliveryMethod === 'sms') {
      const digits = phone.replace(/\D/g, '');
      if (digits.length !== 10) { setError('Please enter a valid 10-digit phone number'); return; }
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) { setError('Please enter a valid email address'); return; }
    }
    if (!consent) { setError('Please agree to the terms to continue'); return; }

    setStep('processing');
    setReportStage(0);
    setError('');

    try {
      const res = await fetch(`/api/proxy/v1/cma/${agentCode}/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: deliveryMethod === 'sms' ? phone.replace(/\D/g, '') : null,
          email: deliveryMethod === 'email' ? email.trim() : null,
          delivery_method: deliveryMethod,
          name: name.trim() || null,
          property_apn: selectedProperty!.apn,
          property_fips: selectedProperty!.fips,
          property_address: selectedProperty!.address,
          property_city: selectedProperty!.city,
          property_state: selectedProperty!.state,
          property_zip: selectedProperty!.zip,
          consent_given: consent,
          owner_name: selectedProperty!.owner_name,
          bedrooms: selectedProperty!.bedrooms,
          bathrooms: selectedProperty!.bathrooms,
          sqft: selectedProperty!.sqft,
          year_built: selectedProperty!.year_built,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || 'Request failed');
      }
      setTimeout(() => setStep('success'), 3000);
    } catch (err: any) {
      setStep('contact');
      setError(err.message || 'Something went wrong. Please try again.');
    }
  };

  // ------- Render -------

  const anim = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
  };

  return (
    <div className="min-h-[300px]">
      <AnimatePresence mode="wait">
        {/* ========== STEP 1: ADDRESS SEARCH ========== */}
        {step === 'address' && (
          <motion.div key="address" {...anim} className="space-y-4">
            <StepIndicator current={1} total={3} color={themeColor} />

            <div className="flex items-center gap-2 mb-1">
              <StepIcon color={themeColor}><MapPin className="w-4 h-4" /></StepIcon>
              <span className="font-medium text-slate-700">Enter Your Address</span>
            </div>

            {searching ? (
              <ProgressStages stages={SEARCH_STAGES} current={searchStage} color={themeColor} icon={<Search className="w-5 h-5" />} />
            ) : (
              <>
                <div className="relative">
                  <Input
                    ref={setAddressInputRef}
                    type="text"
                    placeholder="Start typing your address..."
                    value={address}
                    onChange={e => setAddress(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleManualSearch()}
                    className="text-base h-12 pr-12"
                    autoComplete="off"
                    autoFocus
                  />
                  <button
                    onClick={handleManualSearch}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg hover:bg-slate-100"
                  >
                    <Search className="w-5 h-5 text-slate-400" />
                  </button>
                </div>

                <p className="text-xs text-slate-500">
                  {!googleLoaded && !placesError && 'Loading address suggestions...'}
                  {googleLoaded && !placesError && 'Start typing to see address suggestions'}
                  {placesError && 'Enter your full address'}
                </p>

                {properties.length > 1 && (
                  <div className="space-y-2 mt-2">
                    <p className="text-sm text-slate-600 font-medium">Select your property:</p>
                    {properties.map((prop, i) => (
                      <button
                        key={i}
                        onClick={() => { setSelectedProperty(prop); setStep('confirm'); }}
                        className="w-full p-3 text-left border rounded-xl hover:border-slate-400 hover:bg-slate-50 transition"
                      >
                        <p className="font-medium text-slate-900">{prop.address}</p>
                        <p className="text-sm text-slate-500">
                          {prop.city}, {prop.state} {prop.zip}
                          {prop.owner_name && ` · ${prop.owner_name}`}
                        </p>
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}

            {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          </motion.div>
        )}

        {/* ========== STEP 2: PROPERTY CONFIRMATION ========== */}
        {step === 'confirm' && selectedProperty && (
          <motion.div key="confirm" {...anim} className="space-y-4">
            <StepIndicator current={2} total={3} color={themeColor} />

            <div className="flex items-center gap-2 mb-1">
              <StepIcon color={themeColor}><Home className="w-4 h-4" /></StepIcon>
              <span className="font-medium text-slate-700">We Found Your Property</span>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <p className="font-semibold text-slate-900 text-lg">{selectedProperty.address}</p>
              <p className="text-slate-600 text-sm">
                {selectedProperty.city}, {selectedProperty.state} {selectedProperty.zip}
              </p>

              {(selectedProperty.bedrooms || selectedProperty.bathrooms || selectedProperty.sqft || selectedProperty.year_built) && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                  {selectedProperty.bedrooms != null && (
                    <StatBadge label="Beds" value={String(selectedProperty.bedrooms)} color={themeColor} />
                  )}
                  {selectedProperty.bathrooms != null && (
                    <StatBadge label="Baths" value={String(selectedProperty.bathrooms)} color={themeColor} />
                  )}
                  {selectedProperty.sqft != null && (
                    <StatBadge label="Sq Ft" value={selectedProperty.sqft.toLocaleString()} color={themeColor} />
                  )}
                  {selectedProperty.year_built != null && (
                    <StatBadge label="Built" value={String(selectedProperty.year_built)} color={themeColor} />
                  )}
                </div>
              )}

              {selectedProperty.owner_name && (
                <p className="text-slate-500 text-sm mt-3">Owner: {selectedProperty.owner_name}</p>
              )}
            </div>

            <p className="text-center text-sm text-slate-600">Is this your property?</p>

            <Button
              onClick={handleConfirm}
              className="w-full h-12 text-base text-white"
              style={{ backgroundColor: themeColor }}
            >
              Yes, Get My Report <ChevronRight className="w-4 h-4 ml-1" />
            </Button>

            <button
              onClick={() => { setStep('address'); setSelectedProperty(null); setProperties([]); setSelectedPlace(null); }}
              className="text-sm text-slate-500 hover:text-slate-700 w-full text-center py-1"
            >
              ← Not my property, search again
            </button>
          </motion.div>
        )}

        {/* ========== STEP 3: CONTACT CAPTURE ========== */}
        {step === 'contact' && (
          <motion.div key="contact" {...anim} className="space-y-4">
            <StepIndicator current={3} total={3} color={themeColor} />

            <div className="text-center mb-2">
              <h3 className="text-lg font-semibold text-slate-900">Your Report Is Almost Ready</h3>
              <p className="text-sm text-slate-600 mt-1">Where should we send it?</p>
            </div>

            {/* Report preview */}
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <p className="text-sm font-medium text-slate-700 mb-2">Your report will include:</p>
              <ul className="space-y-1.5 text-sm text-slate-600">
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 flex-shrink-0" style={{ color: themeColor }} /> Estimated home value</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 flex-shrink-0" style={{ color: themeColor }} /> Recent comparable sales</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 flex-shrink-0" style={{ color: themeColor }} /> Neighborhood market trends</li>
                <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 flex-shrink-0" style={{ color: themeColor }} /> Professional PDF report</li>
              </ul>
            </div>

            {/* Delivery method toggle */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setDeliveryMethod('sms')}
                className={`flex items-center justify-center gap-2 p-3 rounded-xl border-2 transition-all text-sm font-medium ${
                  deliveryMethod === 'sms' ? 'text-white' : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
                style={deliveryMethod === 'sms' ? { backgroundColor: themeColor, borderColor: themeColor } : undefined}
              >
                <Phone className="w-4 h-4" /> Text Message
              </button>
              <button
                onClick={() => setDeliveryMethod('email')}
                className={`flex items-center justify-center gap-2 p-3 rounded-xl border-2 transition-all text-sm font-medium ${
                  deliveryMethod === 'email' ? 'text-white' : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
                style={deliveryMethod === 'email' ? { backgroundColor: themeColor, borderColor: themeColor } : undefined}
              >
                <Mail className="w-4 h-4" /> Email
              </button>
            </div>

            {/* Name (optional) */}
            <Input
              type="text"
              placeholder="Your name (optional)"
              value={name}
              onChange={e => setName(e.target.value)}
              className="h-11"
            />

            {/* Contact input */}
            {deliveryMethod === 'sms' ? (
              <Input
                type="tel"
                placeholder="(555) 555-5555"
                value={phone}
                onChange={e => setPhone(formatPhone(e.target.value))}
                className="text-lg text-center h-12"
                autoFocus
              />
            ) : (
              <Input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="text-base h-12"
                autoFocus
              />
            )}

            {/* Consent */}
            <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-xl">
              <Checkbox
                checked={consent}
                onCheckedChange={v => setConsent(v as boolean)}
                id="consent"
                className="mt-0.5"
              />
              <label htmlFor="consent" className="text-sm text-slate-600 leading-tight cursor-pointer">
                I agree to receive my report and to be contacted by {agentName} about my property.
              </label>
            </div>

            {error && <p className="text-red-500 text-sm text-center">{error}</p>}

            <Button
              onClick={handleSubmit}
              disabled={!consent}
              className="w-full h-12 text-base text-white"
              style={{ backgroundColor: themeColor, opacity: consent ? 1 : 0.5 }}
            >
              Generate My Free Report
            </Button>

            <button
              onClick={() => setStep('confirm')}
              className="text-sm text-slate-500 hover:text-slate-700 w-full text-center py-1"
            >
              ← Back
            </button>
          </motion.div>
        )}

        {/* ========== PROCESSING ========== */}
        {step === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-6"
          >
            <ProgressStages stages={REPORT_STAGES} current={reportStage} color={themeColor} icon={<Home className="w-7 h-7 animate-pulse" />} large />
            <p className="text-center text-xs text-slate-500 mt-4">Takes about 15-30 seconds</p>
          </motion.div>
        )}

        {/* ========== SUCCESS ========== */}
        {step === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-6 text-center"
          >
            <div className="relative inline-block mb-4">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${themeColor}20` }}
              >
                <Check className="w-8 h-8" style={{ color: themeColor }} />
              </div>
              <div
                className="absolute inset-0 w-16 h-16 rounded-full border-2 animate-ping"
                style={{ borderColor: `${themeColor}40` }}
              />
            </div>

            <h3 className="text-xl font-semibold text-slate-900 mb-2">Your Report Is Ready!</h3>
            <p className="text-slate-600 mb-4">
              {deliveryMethod === 'sms'
                ? 'Check your text messages for a link to download your free property report.'
                : 'Check your email for your free property report.'}
            </p>

            <div className="bg-slate-50 rounded-xl p-4 text-sm mb-6">
              <p className="text-slate-500">Sent to:</p>
              <p className="font-medium text-slate-900">
                {deliveryMethod === 'sms' ? phone : email}
              </p>
            </div>

            {/* Agent CTA */}
            <div className="bg-slate-50 rounded-xl p-5 text-left">
              <p className="text-sm font-medium text-slate-700 mb-3">
                Questions about your home&apos;s value?
              </p>
              <div className="flex flex-col gap-2">
                {agentPhone && (
                  <a
                    href={`tel:${agentPhone}`}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-white text-sm font-medium"
                    style={{ backgroundColor: themeColor }}
                  >
                    <Phone className="w-4 h-4" /> Call {agentName.split(' ')[0]}
                  </a>
                )}
                {agentEmail && (
                  <a
                    href={`mailto:${agentEmail}`}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium text-slate-700 hover:bg-slate-100"
                  >
                    <Mail className="w-4 h-4" /> Email {agentName.split(' ')[0]}
                  </a>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


// ========== Shared sub-components ==========

function StepIndicator({ current, total, color }: { current: number; total: number; color: string }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-4">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 rounded-full transition-all ${i + 1 <= current ? 'w-8' : 'w-4'}`}
          style={{ backgroundColor: i + 1 <= current ? color : '#E5E7EB' }}
        />
      ))}
    </div>
  );
}

function StepIcon({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <div
      className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ backgroundColor: `${color}20`, color }}
    >
      {children}
    </div>
  );
}

function StatBadge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="text-center p-2 rounded-lg" style={{ backgroundColor: `${color}08` }}>
      <p className="text-base font-bold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}

function ProgressStages({
  stages,
  current,
  color,
  icon,
  large,
}: {
  stages: { id: string; label: string }[];
  current: number;
  color: string;
  icon: React.ReactNode;
  large?: boolean;
}) {
  const size = large ? 'w-20 h-20' : 'w-16 h-16';
  return (
    <div>
      <div className="flex justify-center mb-5">
        <div className="relative">
          <div className={`${size} rounded-full border-4`} style={{ borderColor: `${color}30` }} />
          <div className={`absolute inset-0 ${size} rounded-full border-4 border-transparent animate-spin`} style={{ borderTopColor: color }} />
          <div className="absolute inset-0 flex items-center justify-center" style={{ color }}>{icon}</div>
        </div>
      </div>
      <div className="space-y-2">
        {stages.map((stage, i) => (
          <motion.div
            key={stage.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: i <= current ? 1 : 0.3, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`flex items-center gap-3 p-2 rounded-lg transition-all duration-300 ${
              i < current ? 'text-green-600' : i === current ? '' : 'text-slate-400'
            }`}
            style={{
              backgroundColor: i === current ? `${color}15` : 'transparent',
              color: i === current ? color : undefined,
            }}
          >
            <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
              {i < current ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : i === current ? (
                <Loader2 className="w-5 h-5 animate-spin" style={{ color }} />
              ) : (
                <div className="w-2 h-2 rounded-full bg-current opacity-50" />
              )}
            </div>
            <span className="text-sm font-medium">{stage.label}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
