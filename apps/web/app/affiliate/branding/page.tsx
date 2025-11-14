import { cookies } from 'next/headers';
import { BrandingForm } from '@/components/branding-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Palette, Image, Mail } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

interface BrandingData {
  brand_display_name: string;
  logo_url: string | null;
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
        'Authorization': `Bearer ${token}`,
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">White-Label Branding</h1>
          <p className="text-muted-foreground mt-1">
            Customize how your brand appears on client reports and emails
          </p>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reports</CardTitle>
            <Palette className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Your brand appears on all PDF reports for your sponsored agents
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Emails</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              Scheduled report emails sent to clients display your branding
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">White Label</CardTitle>
            <Image className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xs text-muted-foreground">
              TrendyReports remains invisible to your clients
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Branding Form with Live Preview */}
      <BrandingForm initialData={data} />
    </div>
  );
}

