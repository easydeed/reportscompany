"use client";

import AppLayout from "../../app-layout";
import { API_BASE, DEMO_ACC } from "@/lib/api";
import { useEffect, useState } from "react";

type Account = {
  id: string; name: string; slug: string;
  logo_url?: string; primary_color?: string; secondary_color?: string;
};

export default function BrandingPage() {
  const [acct, setAcct] = useState<Account | null>(null);
  const [logoUrl, setLogoUrl] = useState("");
  const [primary, setPrimary] = useState("#2563EB");
  const [secondary, setSecondary] = useState("#F26B2B");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    const res = await fetch(`${API_BASE}/v1/account`, { headers: { "X-Demo-Account": DEMO_ACC }});
    const j = await res.json();
    setAcct(j);
    setLogoUrl(j.logo_url || "");
    setPrimary(j.primary_color || primary);
    setSecondary(j.secondary_color || secondary);
  }
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  async function save() {
    setSaving(true); setMsg(null);
    const res = await fetch(`${API_BASE}/v1/account/branding`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "X-Demo-Account": DEMO_ACC },
      body: JSON.stringify({ logo_url: logoUrl || null, primary_color: primary, secondary_color: secondary })
    });
    if (!res.ok) {
      const t = await res.text(); setMsg(`Save failed: ${t}`); setSaving(false); return;
    }
    const j = await res.json();
    setAcct(j); setSaving(false); setMsg("Saved!");
  }

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold">Branding</h1>
      <div className="mt-6 grid max-w-2xl gap-4">
        <label className="block">
          <span className="text-sm text-slate-600">Logo URL</span>
          <input value={logoUrl} onChange={e=>setLogoUrl(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" placeholder="https://..." />
        </label>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm text-slate-600">Primary Color</span>
            <input type="text" value={primary} onChange={e=>setPrimary(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" />
          </label>
          <label className="block">
            <span className="text-sm text-slate-600">Secondary Color</span>
            <input type="text" value={secondary} onChange={e=>setSecondary(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" />
          </label>
        </div>

        <button onClick={save} disabled={saving} className="mt-2 w-fit rounded bg-blue-600 px-5 py-2 text-white">
          {saving ? "Saving..." : "Save Changes"}
        </button>
        {msg && <p className="text-sm text-slate-600">{msg}</p>}

        <div className="mt-8 rounded border bg-white p-4">
          <p className="text-sm text-slate-600">Preview</p>
          <div className="mt-3 flex items-center gap-4">
            <div className="h-16 w-16 rounded-lg border bg-white" style={{ backgroundImage: `url(${logoUrl})`, backgroundSize: 'contain', backgroundRepeat: 'no-repeat', backgroundPosition: 'center' }} />
            <div className="flex gap-4">
              <div className="h-10 w-10 rounded" style={{ background: primary }} />
              <div className="h-10 w-10 rounded" style={{ background: secondary }} />
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

