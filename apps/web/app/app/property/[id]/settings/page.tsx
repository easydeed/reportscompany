"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save, RefreshCw, Eye, EyeOff, Calendar, Users, Lock, Unlock } from "lucide-react";

interface ReportSettings {
  id: string;
  property_address: string;
  short_code: string;
  qr_code_url: string | null;
  is_active: boolean;
  expires_at: string | null;
  max_leads: number | null;
  access_code: string | null;
  view_count: number;
  unique_visitors: number;
  last_viewed_at: string | null;
}

export default function PropertyReportSettingsPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;
  
  const [settings, setSettings] = useState<ReportSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [isActive, setIsActive] = useState(true);
  const [expiresAt, setExpiresAt] = useState("");
  const [maxLeads, setMaxLeads] = useState<string>("");
  const [accessCode, setAccessCode] = useState("");
  const [showAccessCode, setShowAccessCode] = useState(false);
  
  useEffect(() => {
    fetchSettings();
  }, [reportId]);
  
  const fetchSettings = async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${apiBase}/v1/property/reports/${reportId}/settings`, {
        credentials: "include",
      });
      
      if (!res.ok) {
        throw new Error("Failed to load settings");
      }
      
      const data = await res.json();
      setSettings(data);
      
      // Initialize form state
      setIsActive(data.is_active);
      setExpiresAt(data.expires_at ? data.expires_at.split("T")[0] : "");
      setMaxLeads(data.max_leads ? String(data.max_leads) : "");
      setAccessCode(data.access_code || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  };
  
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${apiBase}/v1/property/reports/${reportId}/settings`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          is_active: isActive,
          expires_at: expiresAt ? `${expiresAt}T23:59:59Z` : null,
          max_leads: maxLeads ? parseInt(maxLeads) : null,
          access_code: accessCode || null,
        }),
      });
      
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to save settings");
      }
      
      setSuccess("Settings saved successfully!");
      fetchSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };
  
  const handleRegenerateQR = async () => {
    if (!confirm("This will generate a new short code and QR code. The old link will stop working. Continue?")) {
      return;
    }
    
    setRegenerating(true);
    setError(null);
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${apiBase}/v1/property/reports/${reportId}/regenerate-qr`, {
        method: "POST",
        credentials: "include",
      });
      
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to regenerate QR code");
      }
      
      setSuccess("QR code regenerated successfully!");
      fetchSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to regenerate QR code");
    } finally {
      setRegenerating(false);
    }
  };
  
  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/4"></div>
          <div className="h-64 bg-slate-200 rounded"></div>
        </div>
      </div>
    );
  }
  
  if (!settings) {
    return (
      <div className="p-8">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          {error || "Report not found"}
        </div>
      </div>
    );
  }
  
  const publicUrl = `${typeof window !== 'undefined' ? window.location.origin : ''}/p/${settings.short_code}`;
  
  return (
    <div className="p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <Link 
          href={`/app/property/${reportId}`}
          className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Report
        </Link>
        <h1 className="text-2xl font-bold text-slate-900">Landing Page Settings</h1>
        <p className="text-slate-600 mt-1">{settings.property_address}</p>
      </div>
      
      {/* Status Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">
          {success}
        </div>
      )}
      
      <div className="grid gap-6">
        {/* Analytics Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Analytics</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="text-2xl font-bold text-slate-900">{settings.view_count}</div>
              <div className="text-sm text-slate-600">Total Views</div>
            </div>
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="text-2xl font-bold text-slate-900">{settings.unique_visitors}</div>
              <div className="text-sm text-slate-600">Unique Visitors</div>
            </div>
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="text-sm font-medium text-slate-900">
                {settings.last_viewed_at 
                  ? new Date(settings.last_viewed_at).toLocaleDateString()
                  : "Never"
                }
              </div>
              <div className="text-sm text-slate-600">Last Viewed</div>
            </div>
          </div>
        </div>
        
        {/* QR Code Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">QR Code & Link</h2>
          
          <div className="flex items-start gap-6">
            {settings.qr_code_url && (
              <div className="flex-shrink-0">
                <img 
                  src={settings.qr_code_url} 
                  alt="QR Code" 
                  className="w-32 h-32 border border-slate-200 rounded-lg"
                />
              </div>
            )}
            
            <div className="flex-1 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Public URL
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    readOnly
                    value={publicUrl}
                    className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
                  />
                  <button
                    onClick={() => navigator.clipboard.writeText(publicUrl)}
                    className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm font-medium"
                  >
                    Copy
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Short Code
                </label>
                <div className="flex gap-2 items-center">
                  <code className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono">
                    {settings.short_code}
                  </code>
                  <button
                    onClick={handleRegenerateQR}
                    disabled={regenerating}
                    className="inline-flex items-center gap-2 px-3 py-2 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-lg text-sm font-medium disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${regenerating ? "animate-spin" : ""}`} />
                    {regenerating ? "Regenerating..." : "Regenerate"}
                  </button>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Warning: Regenerating will invalidate the current QR code
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Landing Page Controls */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Landing Page Controls</h2>
          
          <div className="space-y-6">
            {/* Active Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isActive ? (
                  <Eye className="w-5 h-5 text-green-600" />
                ) : (
                  <EyeOff className="w-5 h-5 text-slate-400" />
                )}
                <div>
                  <div className="font-medium text-slate-900">Landing Page Active</div>
                  <div className="text-sm text-slate-600">
                    {isActive ? "Page is visible and accepting leads" : "Page is hidden from public"}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setIsActive(!isActive)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out ${
                  isActive ? "bg-green-600" : "bg-slate-200"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    isActive ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
            
            {/* Expiration Date */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2">
                <Calendar className="w-4 h-4" />
                Expires On (optional)
              </label>
              <input
                type="date"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                className="w-full max-w-xs px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-1">
                Leave empty for no expiration
              </p>
            </div>
            
            {/* Max Leads */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2">
                <Users className="w-4 h-4" />
                Maximum Leads (optional)
              </label>
              <input
                type="number"
                value={maxLeads}
                onChange={(e) => setMaxLeads(e.target.value)}
                min="0"
                placeholder="Unlimited"
                className="w-full max-w-xs px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-1">
                Page will stop accepting leads after this number. Leave empty for unlimited.
              </p>
            </div>
            
            {/* Access Code */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-2">
                {accessCode ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                Access Code (optional)
              </label>
              <div className="flex gap-2 max-w-xs">
                <div className="relative flex-1">
                  <input
                    type={showAccessCode ? "text" : "password"}
                    value={accessCode}
                    onChange={(e) => setAccessCode(e.target.value)}
                    placeholder="No password protection"
                    className="w-full px-3 py-2 pr-10 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setShowAccessCode(!showAccessCode)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showAccessCode ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Visitors must enter this code to view the landing page
              </p>
            </div>
          </div>
        </div>
        
        {/* Save Button */}
        <div className="flex justify-end gap-4">
          <Link
            href={`/app/property/${reportId}`}
            className="px-4 py-2 text-slate-700 hover:text-slate-900"
          >
            Cancel
          </Link>
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}

