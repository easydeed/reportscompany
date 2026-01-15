import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ConsumerLandingWizard } from '@/components/lead-pages/ConsumerLandingWizard';
import { getApiBase } from '@/lib/get-api-base';

interface PageProps {
  params: Promise<{ code: string }>;
}

interface AgentInfo {
  name: string;
  photo_url: string | null;
  company_name: string | null;
  phone: string | null;
  email: string | null;
  license_number: string | null;
  headline: string;
  subheadline: string;
  theme_color: string;
}

async function getAgentInfo(code: string): Promise<AgentInfo | null> {
  const apiUrl = getApiBase();
  
  try {
    const res = await fetch(
      `${apiUrl}/v1/cma/${code}`,
      { 
        cache: 'no-store',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!res.ok) {
      console.error(`Failed to fetch agent info: ${res.status}`);
      return null;
    }
    
    return res.json();
  } catch (err) {
    console.error('Error fetching agent info:', err);
    return null;
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const resolvedParams = await params;
  const agent = await getAgentInfo(resolvedParams.code);
  
  if (!agent) {
    return { title: 'Page Not Found' };
  }
  
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

export default async function ConsumerLandingPage({ params }: PageProps) {
  const resolvedParams = await params;
  const agent = await getAgentInfo(resolvedParams.code);
  
  if (!agent) {
    notFound();
  }
  
  return (
    <div 
      className="min-h-screen"
      style={{ 
        background: `linear-gradient(135deg, ${agent.theme_color}10, white, ${agent.theme_color}05)` 
      }}
    >
      {/* Agent Header */}
      <div className="pt-8 pb-4 px-4 text-center">
        {agent.photo_url ? (
          <img
            src={agent.photo_url}
            alt={agent.name}
            className="w-20 h-20 rounded-full mx-auto mb-3 border-4 border-white shadow-lg object-cover"
          />
        ) : (
          <div 
            className="w-20 h-20 rounded-full mx-auto mb-3 border-4 border-white shadow-lg flex items-center justify-center text-white text-2xl font-bold"
            style={{ backgroundColor: agent.theme_color }}
          >
            {agent.name.charAt(0)}
          </div>
        )}
        <h2 className="text-lg font-semibold text-gray-900">{agent.name}</h2>
        {agent.company_name && (
          <p className="text-gray-600 text-sm">{agent.company_name}</p>
        )}
        {agent.license_number && (
          <p className="text-gray-500 text-xs">DRE# {agent.license_number}</p>
        )}
      </div>
      
      {/* Main Card */}
      <div className="max-w-md mx-auto px-4 pb-8">
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <h1 
            className="text-2xl font-bold text-center mb-2"
            style={{ color: agent.theme_color }}
          >
            {agent.headline}
          </h1>
          <p className="text-gray-600 text-center mb-6 text-sm">
            {agent.subheadline}
          </p>
          
          <ConsumerLandingWizard 
            agentCode={resolvedParams.code}
            themeColor={agent.theme_color}
            agentName={agent.name}
          />
        </div>
        
        {/* Trust Badges */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            ✓ 100% Free  ✓ No Obligation  ✓ Results in Seconds
          </p>
        </div>
      </div>
      
      {/* Footer */}
      <div className="text-center pb-6">
        <p className="text-xs text-gray-400">
          Powered by <span className="font-medium">TrendyReports</span>
        </p>
      </div>
    </div>
  );
}

