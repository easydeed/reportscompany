"use client";

import { useState } from "react";

interface LeadCaptureFormProps {
  shortCode: string;
  agentName: string | null;
  accentColor: string;
}

interface FormData {
  name: string;
  email: string;
  phone: string;
  message: string;
  consent_given: boolean;
  website: string;  // Honeypot field - should always be empty
}

type FormStatus = "idle" | "submitting" | "success" | "error" | "rate_limited";

export default function LeadCaptureForm({ 
  shortCode, 
  agentName, 
  accentColor 
}: LeadCaptureFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    email: "",
    phone: "",
    message: "",
    consent_given: false,
    website: "",  // Honeypot - should remain empty
  });
  const [status, setStatus] = useState<FormStatus>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [retryAfter, setRetryAfter] = useState<number | null>(null);
  
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.name.trim() || !formData.email.trim()) {
      setErrorMessage("Please fill in all required fields.");
      setStatus("error");
      return;
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setErrorMessage("Please enter a valid email address.");
      setStatus("error");
      return;
    }
    
    setStatus("submitting");
    setErrorMessage("");
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const response = await fetch(`${apiBase}/v1/leads/capture`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          short_code: shortCode,
          name: formData.name.trim(),
          email: formData.email.trim(),
          phone: formData.phone.trim() || null,
          message: formData.message.trim() || null,
          consent_given: formData.consent_given,
          source: "qr_scan",
          website: formData.website,  // Honeypot field
        }),
      });
      
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        
        // Handle specific error codes
        if (response.status === 429) {
          // Rate limited
          setErrorMessage("You've submitted too many requests. Please try again in an hour.");
          setStatus("rate_limited");
          setRetryAfter(60);  // 60 minutes
          return;
        }
        
        if (response.status === 410) {
          // Page no longer available
          setErrorMessage(data.detail || "This form is no longer accepting submissions.");
          setStatus("error");
          return;
        }
        
        if (response.status === 403) {
          // Blocked or invalid access code
          setErrorMessage(data.detail || "Access denied.");
          setStatus("error");
          return;
        }
        
        throw new Error(data.detail || "Failed to submit form");
      }
      
      setStatus("success");
    } catch (error) {
      console.error("Lead capture error:", error);
      setErrorMessage(
        error instanceof Error 
          ? error.message 
          : "Something went wrong. Please try again."
      );
      setStatus("error");
    }
  };
  
  // Success state
  if (status === "success") {
    return (
      <div className="text-center py-8">
        <div 
          className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
          style={{ backgroundColor: `${accentColor}20` }}
        >
          <svg 
            className="w-8 h-8" 
            fill="none" 
            stroke={accentColor} 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M5 13l4 4L19 7" 
            />
          </svg>
        </div>
        <h4 className="text-xl font-semibold text-slate-900 mb-2">
          Thank You!
        </h4>
        <p className="text-slate-600">
          {agentName ? `${agentName} will` : "We'll"} be in touch with you shortly.
        </p>
      </div>
    );
  }
  
  // Rate limited state
  if (status === "rate_limited") {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 bg-amber-100">
          <svg 
            className="w-8 h-8 text-amber-600" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
        </div>
        <h4 className="text-xl font-semibold text-slate-900 mb-2">
          Please Wait
        </h4>
        <p className="text-slate-600">
          {errorMessage}
        </p>
      </div>
    );
  }
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Honeypot field - hidden from users, catches bots */}
      <div className="absolute -left-[9999px] opacity-0 pointer-events-none" aria-hidden="true">
        <label htmlFor="website">Website</label>
        <input
          type="text"
          id="website"
          name="website"
          value={formData.website}
          onChange={handleChange}
          tabIndex={-1}
          autoComplete="off"
        />
      </div>
      
      {/* Name */}
      <div>
        <label 
          htmlFor="name" 
          className="block text-sm font-medium text-slate-700 mb-1"
        >
          Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          placeholder="Your name"
          className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
          style={{ 
            "--tw-ring-color": accentColor,
          } as React.CSSProperties}
          disabled={status === "submitting"}
        />
      </div>
      
      {/* Email */}
      <div>
        <label 
          htmlFor="email" 
          className="block text-sm font-medium text-slate-700 mb-1"
        >
          Email <span className="text-red-500">*</span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          placeholder="your@email.com"
          className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
          style={{ 
            "--tw-ring-color": accentColor,
          } as React.CSSProperties}
          disabled={status === "submitting"}
        />
      </div>
      
      {/* Phone */}
      <div>
        <label 
          htmlFor="phone" 
          className="block text-sm font-medium text-slate-700 mb-1"
        >
          Phone <span className="text-slate-400">(optional)</span>
        </label>
        <input
          type="tel"
          id="phone"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="(555) 123-4567"
          className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
          style={{ 
            "--tw-ring-color": accentColor,
          } as React.CSSProperties}
          disabled={status === "submitting"}
        />
      </div>
      
      {/* Message */}
      <div>
        <label 
          htmlFor="message" 
          className="block text-sm font-medium text-slate-700 mb-1"
        >
          Message <span className="text-slate-400">(optional)</span>
        </label>
        <textarea
          id="message"
          name="message"
          value={formData.message}
          onChange={handleChange}
          placeholder="I'd like to learn more about this property..."
          rows={3}
          className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all resize-none"
          style={{ 
            "--tw-ring-color": accentColor,
          } as React.CSSProperties}
          disabled={status === "submitting"}
        />
      </div>
      
      {/* Consent */}
      <div className="flex items-start gap-2">
        <input
          type="checkbox"
          id="consent_given"
          name="consent_given"
          checked={formData.consent_given}
          onChange={handleChange}
          className="mt-1 w-4 h-4 rounded border-slate-300"
          style={{ accentColor }}
          disabled={status === "submitting"}
        />
        <label 
          htmlFor="consent_given" 
          className="text-sm text-slate-600"
        >
          I consent to being contacted about this property and related services.
        </label>
      </div>
      
      {/* Error Message */}
      {status === "error" && errorMessage && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {errorMessage}
        </div>
      )}
      
      {/* Submit Button */}
      <button
        type="submit"
        disabled={status === "submitting"}
        className="w-full py-3 px-4 text-white font-medium rounded-lg transition-all hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed"
        style={{ backgroundColor: accentColor }}
      >
        {status === "submitting" ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle 
                className="opacity-25" 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="4"
              />
              <path 
                className="opacity-75" 
                fill="currentColor" 
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Sending...
          </span>
        ) : (
          "Get More Information"
        )}
      </button>
      
      <p className="text-xs text-slate-500 text-center">
        Your information is secure and will only be shared with the listing agent.
      </p>
    </form>
  );
}

