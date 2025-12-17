import { cookies } from 'next/headers';
import { BrandingForm } from '@/components/branding-form';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, Sparkles } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

interface BrandingData {
  brand_display_name: string;
  logo_url: string | null;
  footer_logo_url: string | null;
  primary_color: string | null;
  accent_color: string | null;
  rep_photo_url: string | null;
  contact_line1: string | null;
  contact_line2: string | null;
  website_url: string | null;
}

async function getBranding(): Promise<BrandingData | { error: string }> {
  const cookieStore = await cookies();
  const token = cookieStore.get('mr_token')?.value;

  if (!token) {
    return { error: 'Not authenticated' };
  }

  try {
    const response = await fetch(`${API_BASE}/v1/affiliate/branding`, {
      headers: {
        'Cookie': `mr_token=${token}`,
      },
      cache: 'no-store',
    });

    if (response.status === 403) {
      return { error: 'not_affiliate' };
    }

    if (!response.ok) {
      return { error: 'Failed to load branding' };
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch branding:', error);
    return { error: 'Failed to load branding' };
  }
}

export default async function AffiliateBrandingPage() {
  const data = await getBranding();

  // Handle errors
  if ('error' in data) {
    if (data.error === 'not_affiliate') {
      return (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold tracking-tight">Branding</h1>
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 text-muted-foreground">
                <AlertCircle className="h-5 w-5" />
                <p>This account is not an industry affiliate.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Branding</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">{data.error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-violet-600 to-orange-500 p-8 text-white">
        <div className="absolute inset-0 bg-black/10" />
        <div className="relative flex items-center gap-4">
          <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
            <Sparkles className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">White-Label Branding</h1>
            <p className="text-white/80 mt-1 max-w-xl">
              Create a professional, branded experience for your clients. Your logo and colors 
              appear on all PDF reports and emails — TrendyReports stays behind the scenes.
            </p>
          </div>
        </div>
        {/* Decorative elements */}
        <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-white/10 rounded-full blur-xl" />
        <div className="absolute -right-16 -top-8 w-24 h-24 bg-white/10 rounded-full blur-lg" />
      </div>

      {/* Branding Form with Live Preview */}
      <BrandingForm initialData={data} />
    </div>
  );
}

