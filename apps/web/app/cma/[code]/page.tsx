import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { CmaFunnel } from './cma-funnel';
import { getApiBase } from '@/lib/get-api-base';

interface PageProps {
  params: Promise<{ code: string }>;
  searchParams: Promise<{ address?: string }>;
}

export interface AgentInfo {
  name: string;
  photo_url: string | null;
  company_name: string | null;
  phone: string | null;
  email: string | null;
  license_number: string | null;
  headline: string;
  subheadline: string;
  theme_color: string;
  logo_url: string | null;
  website_url: string | null;
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
        <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">{title}</h1>
        <p className="text-slate-600 mb-6">{message}</p>
        <p className="text-sm text-slate-400">Powered by <span className="font-medium">TrendyReports</span></p>
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

  const tc = agent.theme_color;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Gradient Hero */}
      <div
        className="relative overflow-hidden"
        style={{
          background: `linear-gradient(135deg, ${tc} 0%, ${tc}dd 50%, ${tc}aa 100%)`,
        }}
      >
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />

        <div className="relative z-10 pt-6 pb-10 px-4 text-center max-w-md mx-auto">
          {/* Logo */}
          {agent.logo_url && (
            <img
              src={agent.logo_url}
              alt={agent.company_name || 'Company'}
              className="h-10 w-auto mx-auto mb-6 object-contain filter brightness-0 invert"
            />
          )}

          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2 drop-shadow-lg">
            {agent.headline}
          </h1>
          <p className="text-white/90 text-base md:text-lg drop-shadow">
            {agent.subheadline}
          </p>
        </div>
      </div>

      {/* Main content card — overlapping hero */}
      <div className="max-w-md mx-auto px-4 -mt-6 relative z-20 pb-10">
        {/* Agent Card */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-4">
          <div className="p-5 flex items-center gap-4">
            {agent.photo_url ? (
              <img
                src={agent.photo_url}
                alt={agent.name}
                className="w-16 h-16 rounded-full object-cover shadow-md border-2 border-white flex-shrink-0"
              />
            ) : (
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center text-white text-xl font-bold shadow-md flex-shrink-0"
                style={{ backgroundColor: tc }}
              >
                {agent.name.charAt(0)}
              </div>
            )}
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-slate-900 truncate">{agent.name}</h2>
              {agent.company_name && (
                <p className="text-slate-600 text-sm truncate">{agent.company_name}</p>
              )}
              {agent.license_number && (
                <p className="text-slate-400 text-xs">DRE# {agent.license_number}</p>
              )}
            </div>
          </div>
        </div>

        {/* Funnel Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <CmaFunnel
            agentCode={code}
            themeColor={tc}
            agentName={agent.name}
            agentPhone={agent.phone}
            agentEmail={agent.email}
            prefillAddress={prefillAddress}
          />
        </div>

        {/* Trust badges */}
        <div className="mt-4 text-center">
          <p className="text-xs text-slate-500">
            ✓ 100% Free &nbsp; ✓ No Obligation &nbsp; ✓ Results in Seconds
          </p>
        </div>
      </div>

      <div className="text-center pb-6">
        <p className="text-xs text-slate-400">
          Powered by <span className="font-medium">TrendyReports</span>
        </p>
      </div>
    </div>
  );
}
