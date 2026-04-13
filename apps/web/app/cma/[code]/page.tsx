import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { CmaFunnel } from './cma-funnel';
import { getApiBase } from '@/lib/get-api-base';
import { Phone, Mail, Globe, Shield } from 'lucide-react';

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
  const ac = agent.accent_color;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Gradient Hero — matches email banner */}
      <div className="relative overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, ${tc} 0%, ${ac} 100%)`,
          }}
        />
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />

        <div className="relative z-10 pt-6 pb-16 px-4 text-center max-w-md mx-auto">
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

      {/* Content section with subtle background texture */}
      <div className="relative">
        <div
          className="absolute inset-0 overflow-hidden"
        >
          <div
            className="absolute inset-0 grayscale"
            style={{
              backgroundImage: "url('https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1600&q=80')",
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
          />
          <div className="absolute inset-0 bg-white/[0.92]" />
        </div>

        <div className="relative z-10">
          <div className="max-w-md mx-auto px-4 -mt-8 relative z-20 pb-10">
            {/* Agent Card — centered layout with photo inside */}
            <div className="rounded-2xl bg-white px-6 pb-5 pt-6 shadow-xl mb-4" style={{ '--theme-color': tc } as React.CSSProperties}>
              {/* Photo / Initials */}
              <div className="flex justify-center mb-4">
                {agent.photo_url ? (
                  <div
                    className="h-24 w-24 overflow-hidden rounded-full border-[3px] border-white"
                    style={{ boxShadow: '0 4px 14px rgba(0,0,0,0.15)' }}
                  >
                    <img
                      src={agent.photo_url}
                      alt={agent.name}
                      className="h-full w-full object-cover"
                    />
                  </div>
                ) : (
                  <div
                    className="flex h-24 w-24 items-center justify-center rounded-full border-[3px] border-white text-2xl font-bold text-white"
                    style={{
                      backgroundColor: tc,
                      boxShadow: '0 4px 14px rgba(0,0,0,0.15)',
                    }}
                  >
                    {agent.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                  </div>
                )}
              </div>

              {/* Name & Title */}
              <div className="text-center">
                <h2 className="text-[22px] font-bold text-gray-800">{agent.name}</h2>
                {agent.job_title && (
                  <p className="mt-1 text-sm font-medium" style={{ color: tc }}>{agent.job_title}</p>
                )}
                {agent.company_name && (
                  <div className="mt-2 flex items-center justify-center gap-2">
                    {agent.logo_url && (
                      <img src={agent.logo_url} alt={agent.company_name} className="h-4 w-auto object-contain" />
                    )}
                    <span className="text-[13px] text-gray-500">{agent.company_name}</span>
                  </div>
                )}
                {agent.license_number && (
                  <p className="mt-1 text-[11px] text-gray-400">DRE# {agent.license_number}</p>
                )}
              </div>

              {/* Contact Pills */}
              {(agent.phone || agent.email || agent.website_url) && (
                <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                  {agent.phone && (
                    <a
                      href={`tel:${agent.phone.replace(/\D/g, '')}`}
                      className="inline-flex min-h-[44px] items-center gap-2 rounded-full border border-gray-200 px-4 py-2 text-sm text-gray-700 transition-all hover:border-[color:var(--theme-color)] hover:bg-gray-50"
                    >
                      <Phone className="h-3.5 w-3.5" style={{ color: tc }} />
                      <span>{agent.phone}</span>
                    </a>
                  )}
                  {agent.email && (
                    <a
                      href={`mailto:${agent.email}`}
                      className="inline-flex min-h-[44px] items-center gap-2 rounded-full border border-gray-200 px-4 py-2 text-sm text-gray-700 transition-all hover:border-[color:var(--theme-color)] hover:bg-gray-50"
                    >
                      <Mail className="h-3.5 w-3.5" style={{ color: tc }} />
                      <span>Email</span>
                    </a>
                  )}
                  {agent.website_url && (
                    <a
                      href={agent.website_url.startsWith('http') ? agent.website_url : `https://${agent.website_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex min-h-[44px] items-center gap-2 rounded-full border border-gray-200 px-4 py-2 text-sm text-gray-700 transition-all hover:border-[color:var(--theme-color)] hover:bg-gray-50"
                    >
                      <Globe className="h-3.5 w-3.5" style={{ color: tc }} />
                      <span>Website</span>
                    </a>
                  )}
                </div>
              )}

              {/* Trust Indicators */}
              <div className="mt-5 border-t border-gray-100 pt-4">
                <div className="flex items-center justify-center gap-4 text-[11px] text-gray-400">
                  <div className="flex items-center gap-1.5">
                    <Shield className="h-3.5 w-3.5" />
                    <span>Licensed Agent</span>
                  </div>
                  {agent.logo_url && agent.company_name && (
                    <div className="flex items-center gap-1.5">
                      <img src={agent.logo_url} alt="" className="h-3 w-auto opacity-60" />
                      <span>Verified</span>
                    </div>
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
      </div>
    </div>
  );
}
