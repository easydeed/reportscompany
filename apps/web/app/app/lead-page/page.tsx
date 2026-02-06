import { cookies } from 'next/headers';
import { getApiBase } from '@/lib/get-api-base';
import { LeadPageClient } from './lead-page-client';

interface LeadPageSettings {
  agent_code: string;
  url: string;
  qr_code_url: string;
  full_name: string;
  photo_url: string | null;
  company_name: string | null;
  phone: string | null;
  email: string | null;
  license_number: string | null;
  headline: string;
  subheadline: string;
  theme_color: string;
  enabled: boolean;
  visits: number;
}

interface ConsumerLead {
  id: string;
  consumer_phone: string;
  consumer_email: string | null;
  property_address: string;
  property_city: string;
  property_state: string;
  property_zip: string;
  status: string;
  view_count: number;
  agent_contact_clicked: boolean;
  agent_contact_type: string | null;
  pdf_downloaded: boolean;
  created_at: string;
  updated_at: string;
}

async function fetchWithAuth(path: string, token: string) {
  try {
    const API_BASE = getApiBase();
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Cookie': `mr_token=${token}` },
      cache: 'no-store',
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export default async function LeadPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get('mr_token')?.value;

  let settings: LeadPageSettings | null = null;
  let leads: ConsumerLead[] = [];

  if (token) {
    // Fetch both in parallel - server-side, no loading flash
    const [settingsRes, leadsRes] = await Promise.all([
      fetchWithAuth('/v1/me/lead-page', token),
      fetchWithAuth('/v1/me/leads', token),
    ]);

    settings = settingsRes;
    leads = leadsRes?.leads || [];
  }

  return <LeadPageClient initialSettings={settings} initialLeads={leads} />;
}
