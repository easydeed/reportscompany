"use client";
import AppLayout from "../app-layout";
import { API_BASE, DEMO_ACC } from "@/lib/api";
import { useEffect, useState } from "react";

type BillingState = { plan_slug?: string; billing_status?: string; stripe_customer_id?: string | null; };
async function fetchAccount(): Promise<BillingState> {
  const r = await fetch(`${API_BASE}/v1/account`, { headers: { "X-Demo-Account": DEMO_ACC }});
  return r.ok ? r.json() : {};
}

export default function BillingPage(){
  const [acct, setAcct] = useState<BillingState>({});
  const [loading, setLoading] = useState(false);

  useEffect(()=>{ fetchAccount().then(setAcct); }, []);

  async function checkout(plan: "starter"|"professional"|"enterprise"){
    setLoading(true);
    const r = await fetch(`${API_BASE}/v1/billing/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Demo-Account": DEMO_ACC },
      body: JSON.stringify({ plan })
    });
    const j = await r.json(); setLoading(false);
    if (j.url) window.location.href = j.url;
  }

  async function portal(){
    const r = await fetch(`${API_BASE}/v1/billing/portal`, { headers: { "X-Demo-Account": DEMO_ACC }});
    const j = await r.json();
    if (j.url) window.location.href = j.url;
  }

  return (
    <AppLayout>
      <h1 className="text-2xl font-semibold">Billing</h1>
      <div className="mt-2 text-sm text-slate-600">
        Plan: <b>{acct.plan_slug || "—"}</b> · Status: <b>{acct.billing_status || "—"}</b>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded border bg-white p-4">
          <h3 className="font-medium">Starter</h3>
          <p className="text-sm text-slate-600">100 reports / mo</p>
          <button onClick={()=>checkout("starter")} disabled={loading} className="mt-3 rounded bg-blue-600 px-4 py-2 text-white">Choose Starter</button>
        </div>
        <div className="rounded border bg-white p-4">
          <h3 className="font-medium">Professional</h3>
          <p className="text-sm text-slate-600">500 reports / mo • API • Branding</p>
          <button onClick={()=>checkout("professional")} disabled={loading} className="mt-3 rounded bg-blue-600 px-4 py-2 text-white">Choose Professional</button>
        </div>
        <div className="rounded border bg-white p-4">
          <h3 className="font-medium">Enterprise</h3>
          <p className="text-sm text-slate-600">Unlimited • White-label</p>
          <button onClick={()=>checkout("enterprise")} disabled={loading} className="mt-3 rounded bg-blue-600 px-4 py-2 text-white">Choose Enterprise</button>
        </div>
      </div>

      <div className="mt-6">
        <button onClick={portal} className="rounded border px-4 py-2">Open Billing Portal</button>
      </div>
    </AppLayout>
  );
}

