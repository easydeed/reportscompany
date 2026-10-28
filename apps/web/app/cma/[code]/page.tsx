import { Metadata } from 'next';
import { CmaExperience } from './cma-client';
import { getApiBase } from '@/lib/get-api-base';

interface PageProps {
  params: Promise<{ code: string }>;
  searchParams: Promise<{ address?: string }>;
}

export interface AgentInfo {
  name: string;
  job_title: string | null;
  photo_url: string | null;
  company_name: string | null;
  phone: string | null;
  email: string | null;
  license_number: string | null;
  headline: string;
  subheadline: string;
  theme_color: string;
  accent_color: string;
  logo_url: string | null;
  website_url: string | null;
  is_demo?: boolean;
}

async function getAgentInfo(code: string): Promise<AgentInfo | null> {
  const apiUrl = getApiBase();
  try {
    const res = await fetch(`${apiUrl}/v1/cma/${code}`, {
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { code } = await params;
  const agent = await getAgentInfo(code);
  if (!agent) return { title: 'Page Not Found' };

  return {
    title: `${agent.headline} | ${agent.name}`,
    description: agent.subheadline,
    openGraph: {
      title: agent.headline,
      description: agent.subheadline,
      type: 'website',
    },
  };
}

function StatusPage({ title, message }: { title: string; message: string }) {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">{title}</h1>
        <p className="text-slate-600">{message}</p>
      </div>
    </div>
  );
}

export default async function CmaLandingPage({ params, searchParams }: PageProps) {
  const { code } = await params;
  const { address: prefillAddress } = await searchParams;
  const agent = await getAgentInfo(code);

  if (!agent) {
    return (
      <StatusPage
        title="Page Not Found"
        message="This agent page doesn't exist or has been deactivated."
      />
    );
  }

  return (
    <CmaExperience
      code={code}
      isDemo={agent.is_demo === true}
      initialAddress={prefillAddress}
      source={{
        name: agent.name,
        company_name: agent.company_name,
        license_number: agent.license_number,
        phone: agent.phone,
        photo_url: agent.photo_url,
        theme_color: agent.theme_color,
      }}
    />
  );
}
