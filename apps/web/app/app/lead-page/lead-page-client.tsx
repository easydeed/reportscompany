'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import { MetricCard } from '@/components/metric-card';
import { StatusBadge } from '@/components/status-badge';
import {
  Copy, ExternalLink, QrCode, Download,
  Phone, Eye, Clock, FileText, TrendingUp,
  Settings, Loader2, CheckCircle, Flame,
  Share2
} from 'lucide-react';
import { toast } from 'sonner';
import { apiFetch } from '@/lib/api';

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

interface LeadPageClientProps {
  initialSettings: LeadPageSettings | null;
  initialLeads: ConsumerLead[];
}

export function LeadPageClient({ initialSettings, initialLeads }: LeadPageClientProps) {
  const [settings, setSettings] = useState<LeadPageSettings | null>(initialSettings);
  const [leads, setLeads] = useState<ConsumerLead[]>(initialLeads);
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState<'all' | 'hot' | 'contacted'>('all');
  
  const [headline, setHeadline] = useState(initialSettings?.headline || '');
  const [subheadline, setSubheadline] = useState(initialSettings?.subheadline || '');
  const [themeColor, setThemeColor] = useState(initialSettings?.theme_color || '#818CF8');
  const [enabled, setEnabled] = useState(initialSettings?.enabled !== false);
  const [agentCode, setAgentCode] = useState(initialSettings?.agent_code || '');
  const [showSettings, setShowSettings] = useState(false);
  const [codeError, setCodeError] = useState('');

  const saveSettings = async () => {
    setSaving(true);
    setCodeError('');
    try {
      const payload: Record<string, unknown> = {
        headline,
        subheadline,
        theme_color: themeColor,
        enabled,
      };
      if (agentCode && agentCode !== settings?.agent_code) {
        payload.agent_code = agentCode;
      }
      const updated = await apiFetch('/v1/me/lead-page', {
        method: 'PATCH',
        body: JSON.stringify(payload),
      });
      
      setSettings(updated);
      setAgentCode(updated.agent_code);
      toast.success('Settings saved!');
      setShowSettings(false);
      
    } catch (err: any) {
      const msg = err?.message || '';
      if (msg.includes('already taken') || msg.includes('409')) {
        setCodeError('This agent code is already taken. Try another.');
      } else {
        console.error('Failed to save settings', err);
        toast.error('Failed to save settings');
      }
    } finally {
      setSaving(false);
    }
  };

  const copyUrl = () => {
    if (settings?.url) {
      navigator.clipboard.writeText(settings.url);
      toast.success('URL copied to clipboard!');
    }
  };

  const shareUrl = async () => {
    if (settings?.url && navigator.share) {
      try {
        await navigator.share({
          title: settings.headline,
          text: 'Get your free home value report',
          url: settings.url,
        });
      } catch (err) {
        // User cancelled or share failed - copy to clipboard instead
        copyUrl();
      }
    } else {
      copyUrl();
    }
  };

  const downloadQR = () => {
    if (settings?.qr_code_url) {
      const link = document.createElement('a');
      link.href = settings.qr_code_url;
      link.download = `lead-page-qr-${settings.agent_code}.png`;
      link.click();
    }
  };

  // Filter leads
  const filteredLeads = leads.filter(lead => {
    if (filter === 'hot') return lead.view_count > 1 || lead.agent_contact_clicked;
    if (filter === 'contacted') return lead.agent_contact_clicked;
    return true;
  });

  // Calculate stats
  const stats = {
    totalLeads: leads.length,
    hotLeads: leads.filter(l => l.view_count > 1 || l.agent_contact_clicked).length,
    contactedLeads: leads.filter(l => l.agent_contact_clicked).length,
    conversionRate: leads.length > 0 
      ? Math.round(leads.filter(l => l.agent_contact_clicked).length / leads.length * 100)
      : 0,
  };

  // No loading state needed - data comes from server
  if (!settings) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">Failed to load lead page settings</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="My Leads"
        description="Share your link to capture leads automatically"
        action={
          <Button size="sm" onClick={() => setShowSettings(!showSettings)}>
            <Settings className="w-4 h-4 mr-1.5" />
            Settings
          </Button>
        }
      />

      {/* Settings Panel (Collapsible) */}
      {showSettings && (
        <Card className="border-indigo-200 bg-indigo-50/50">
          <CardHeader>
            <CardTitle className="text-lg">Customize Your Lead Page</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Agent Code</Label>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-sm text-muted-foreground whitespace-nowrap">trendyreports.io/cma/</span>
                <Input
                  value={agentCode}
                  onChange={(e) => {
                    setAgentCode(e.target.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase());
                    setCodeError('');
                  }}
                  placeholder="SARAHC2025"
                  className="w-40 font-mono uppercase"
                  maxLength={20}
                />
              </div>
              {codeError && <p className="text-sm text-red-500 mt-1">{codeError}</p>}
              <p className="text-xs text-muted-foreground mt-1">3-20 alphanumeric characters. This is your permanent shareable URL.</p>
            </div>
            <div>
              <Label>Headline</Label>
              <Input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="What's Your Home Worth?"
              />
            </div>
            <div>
              <Label>Subheadline</Label>
              <Input
                value={subheadline}
                onChange={(e) => setSubheadline(e.target.value)}
                placeholder="Get a free, professional property report in seconds."
              />
            </div>
            <div className="flex items-center gap-4">
              <div>
                <Label>Theme Color</Label>
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="color"
                    value={themeColor}
                    onChange={(e) => setThemeColor(e.target.value)}
                    className="w-10 h-10 rounded border cursor-pointer"
                  />
                  <Input
                    value={themeColor}
                    onChange={(e) => setThemeColor(e.target.value)}
                    className="w-28"
                    maxLength={7}
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={enabled}
                  onCheckedChange={setEnabled}
                />
                <Label>Page Enabled</Label>
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <Button onClick={saveSettings} disabled={saving}>
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Save Changes
              </Button>
              <Button variant="outline" onClick={() => setShowSettings(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Your Lead Page Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-600" />
            Your Shareable Lead Page
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            {/* URL Section */}
            <div>
              <Label className="text-sm font-medium text-foreground mb-2 block">
                Your Unique URL
              </Label>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-muted/60 px-4 py-3 rounded-lg font-mono text-sm truncate">
                  {settings.url}
                </div>
                <Button variant="outline" size="icon" onClick={copyUrl} title="Copy URL">
                  <Copy className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={shareUrl} title="Share">
                  <Share2 className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="icon" asChild title="Open in new tab">
                  <a href={settings.url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Share this link on business cards, social media, email signatures, yard signs, etc.
              </p>
            </div>

            {/* QR Code Section */}
            <div>
              <Label className="text-sm font-medium text-foreground mb-2 block">
                Your QR Code
              </Label>
              <div className="flex items-center gap-4">
                <div className="bg-white border rounded-xl p-3">
                  {settings.qr_code_url ? (
                    <img 
                      src={settings.qr_code_url} 
                      alt="QR Code"
                      className="w-24 h-24"
                    />
                  ) : (
                    <div className="w-24 h-24 bg-muted/60 rounded flex items-center justify-center">
                      <QrCode className="w-8 h-8 text-muted-foreground/60" />
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={downloadQR}
                    className="w-full"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download QR
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6 pt-6 border-t border-border">
            <MetricCard label="Page Visits" value={settings.visits || 0} icon={<Eye className="w-4 h-4" />} index={0} />
            <MetricCard label="Leads Captured" value={stats.totalLeads} icon={<FileText className="w-4 h-4" />} index={1} />
            <MetricCard label="Hot Leads" value={stats.hotLeads} icon={<Flame className="w-4 h-4" />} index={2} />
            <MetricCard label="Contact Rate" value={`${stats.conversionRate}%`} icon={<TrendingUp className="w-4 h-4" />} index={3} />
          </div>
        </CardContent>
      </Card>

      {/* Leads List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Your Leads</CardTitle>
            <div className="flex items-center gap-2">
              <Button 
                variant={filter === 'all' ? 'default' : 'outline'} 
                size="sm"
                onClick={() => setFilter('all')}
              >
                All ({leads.length})
              </Button>
              <Button 
                variant={filter === 'hot' ? 'default' : 'outline'} 
                size="sm"
                onClick={() => setFilter('hot')}
              >
                <Flame className="w-3 h-3 mr-1" />
                Hot ({stats.hotLeads})
              </Button>
              <Button 
                variant={filter === 'contacted' ? 'default' : 'outline'} 
                size="sm"
                onClick={() => setFilter('contacted')}
              >
                <CheckCircle className="w-3 h-3 mr-1" />
                Contacted ({stats.contactedLeads})
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredLeads.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>
                {filter === 'all' 
                  ? 'No leads yet. Share your URL to start capturing leads!'
                  : `No ${filter} leads found.`
                }
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredLeads.map((lead) => (
                <LeadRow key={lead.id} lead={lead} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


function LeadRow({ lead }: { lead: ConsumerLead }) {
  const isHot = lead.view_count > 1 || lead.agent_contact_clicked;
  
  return (
    <div className={`p-4 rounded-xl border ${isHot ? 'border-amber-200 bg-amber-50' : 'border-border bg-muted'}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-foreground truncate">
              {lead.property_address}
            </p>
            {isHot && (
              <StatusBadge status="new" label="Hot" />
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {lead.property_city}, {lead.property_state} {lead.property_zip}
          </p>
          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Phone className="w-3 h-3" />
              {lead.consumer_phone}
            </span>
            <span className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              {lead.view_count} view{lead.view_count !== 1 ? 's' : ''}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(lead.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {lead.agent_contact_clicked && (
            <StatusBadge status="contacted" />
          )}
          {lead.pdf_downloaded && (
            <StatusBadge status="delivered" label="PDF" />
          )}
          <a 
            href={`tel:${lead.consumer_phone}`}
            className="p-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Phone className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
