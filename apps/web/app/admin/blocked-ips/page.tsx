"use client";

import { useState, useEffect } from "react";
import { Shield, Plus, Trash2, Search, Clock, AlertTriangle, RefreshCw } from "lucide-react";

interface BlockedIP {
  id: string;
  ip_address: string;
  reason: string | null;
  blocked_by_email: string | null;
  created_at: string;
  expires_at: string | null;
}

export default function BlockedIPsPage() {
  const [blockedIPs, setBlockedIPs] = useState<BlockedIP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Add IP form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newIP, setNewIP] = useState("");
  const [newReason, setNewReason] = useState("");
  const [newExpiry, setNewExpiry] = useState("");
  const [adding, setAdding] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<{expired: number, rate_limits: number} | null>(null);
  
  useEffect(() => {
    fetchBlockedIPs();
  }, []);
  
  const fetchBlockedIPs = async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${apiBase}/v1/admin/blocked-ips`, {
        credentials: "include",
      });
      
      if (!res.ok) {
        throw new Error("Failed to load blocked IPs");
      }
      
      const data = await res.json();
      setBlockedIPs(data.blocked_ips || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };
  
  const handleAddIP = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newIP.trim()) {
      return;
    }
    
    setAdding(true);
    setError(null);
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${apiBase}/v1/admin/blocked-ips`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ip_address: newIP.trim(),
          reason: newReason.trim() || null,
          expires_at: newExpiry ? `${newExpiry}T23:59:59Z` : null,
        }),
      });
      
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to block IP");
      }
      
      // Reset form and refresh
      setNewIP("");
      setNewReason("");
      setNewExpiry("");
      setShowAddForm(false);
      fetchBlockedIPs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add");
    } finally {
      setAdding(false);
    }
  };
  
  const handleDeleteIP = async (id: string, ipAddress: string) => {
    if (!confirm(`Unblock IP ${ipAddress}?`)) {
      return;
    }
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${apiBase}/v1/admin/blocked-ips/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      
      if (!res.ok) {
        throw new Error("Failed to unblock IP");
      }
      
      fetchBlockedIPs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  };
  
  const handleCleanup = async () => {
    setCleaning(true);
    setError(null);
    setCleanupResult(null);
    
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || "";
      const res = await fetch(`${apiBase}/v1/admin/blocked-ips/cleanup`, {
        method: "POST",
        credentials: "include",
      });
      
      if (!res.ok) {
        throw new Error("Failed to run cleanup");
      }
      
      const data = await res.json();
      setCleanupResult({
        expired: data.expired_blocks_removed,
        rate_limits: data.rate_limits_removed,
      });
      fetchBlockedIPs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cleanup failed");
    } finally {
      setCleaning(false);
    }
  };
  
  const filteredIPs = blockedIPs.filter(ip =>
    ip.ip_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (ip.reason && ip.reason.toLowerCase().includes(searchTerm.toLowerCase()))
  );
  
  const isExpired = (expiresAt: string | null) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };
  
  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
            <Shield className="w-7 h-7 text-red-600" />
            Blocked IPs
          </h1>
          <p className="text-slate-600 mt-1">
            Manage IP addresses blocked from submitting leads
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCleanup}
            disabled={cleaning}
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${cleaning ? "animate-spin" : ""}`} />
            {cleaning ? "Cleaning..." : "Cleanup Expired"}
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium"
          >
            <Plus className="w-4 h-4" />
            Block IP
          </button>
        </div>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}
      
      {/* Cleanup Result */}
      {cleanupResult && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">
          Cleanup complete: Removed {cleanupResult.expired} expired blocks and {cleanupResult.rate_limits} old rate limit records.
        </div>
      )}
      
      {/* Add IP Form */}
      {showAddForm && (
        <div className="mb-6 bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Block New IP</h2>
          <form onSubmit={handleAddIP} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  IP Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newIP}
                  onChange={(e) => setNewIP(e.target.value)}
                  placeholder="192.168.1.1 or 2001:db8::1"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Reason
                </label>
                <input
                  type="text"
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  placeholder="Spam submissions"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Expires On (optional)
                </label>
                <input
                  type="date"
                  value={newExpiry}
                  onChange={(e) => setNewExpiry(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 text-slate-700 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={adding}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium disabled:opacity-50"
              >
                {adding ? "Blocking..." : "Block IP"}
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by IP or reason..."
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="text-2xl font-bold text-slate-900">{blockedIPs.length}</div>
          <div className="text-sm text-slate-600">Total Blocked IPs</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="text-2xl font-bold text-slate-900">
            {blockedIPs.filter(ip => !ip.expires_at).length}
          </div>
          <div className="text-sm text-slate-600">Permanent Blocks</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="text-2xl font-bold text-amber-600">
            {blockedIPs.filter(ip => ip.expires_at && isExpired(ip.expires_at)).length}
          </div>
          <div className="text-sm text-slate-600">Expired (cleanup needed)</div>
        </div>
      </div>
      
      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Loading...</div>
        ) : filteredIPs.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            {searchTerm ? "No matching IPs found" : "No blocked IPs"}
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-700">IP Address</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-700">Reason</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-700">Blocked By</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-700">Blocked At</th>
                <th className="text-left px-4 py-3 text-sm font-semibold text-slate-700">Expires</th>
                <th className="text-right px-4 py-3 text-sm font-semibold text-slate-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredIPs.map((ip) => (
                <tr key={ip.id} className={`hover:bg-slate-50 ${isExpired(ip.expires_at) ? "opacity-50" : ""}`}>
                  <td className="px-4 py-3">
                    <code className="text-sm font-mono bg-slate-100 px-2 py-1 rounded">
                      {ip.ip_address}
                    </code>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {ip.reason || <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {ip.blocked_by_email || <span className="text-slate-400">System</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {new Date(ip.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {ip.expires_at ? (
                      <span className={`inline-flex items-center gap-1 ${isExpired(ip.expires_at) ? "text-amber-600" : "text-slate-600"}`}>
                        <Clock className="w-4 h-4" />
                        {new Date(ip.expires_at).toLocaleDateString()}
                        {isExpired(ip.expires_at) && " (expired)"}
                      </span>
                    ) : (
                      <span className="text-red-600 font-medium">Permanent</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDeleteIP(ip.id, ip.ip_address)}
                      className="inline-flex items-center gap-1 px-2 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                      Unblock
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

