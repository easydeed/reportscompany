'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
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

export default function AgentLeadPageDashboard() {
  const [settings, setSettings] = useState<LeadPageSettings | null>(null);
  const [leads, setLeads] = useState<ConsumerLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState<'all' | 'hot' | 'contacted'>('all');
  
  // Editable settings
  const [headline, setHeadline] = useState('');
  const [subheadline, setSubheadline] = useState('');
  const [themeColor, setThemeColor] = useState('#8B5CF6');
  const [enabled, setEnabled] = useState(true);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [settingsRes, leadsRes] = await Promise.all([
        apiFetch('/v1/me/lead-page'),
        apiFetch('/v1/me/leads')
      ]);
      
      setSettings(settingsRes);
      setLeads(leadsRes.leads || []);
      
      // Set editable values
      setHeadline(settingsRes.headline || '');
      setSubheadline(settingsRes.subheadline || '');
      setThemeColor(settingsRes.theme_color || '#8B5CF6');
      setEnabled(settingsRes.enabled !== false);
      
    } catch (err) {
      console.error('Failed to fetch data', err);
      toast.error('Failed to load lead page data');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const updated = await apiFetch('/v1/me/lead-page', {
        method: 'PATCH',
        body: JSON.stringify({
          headline,
          subheadline,
          theme_color: themeColor,
          enabled,
        }),
      });
      
      setSettings(updated);
      toast.success('Settings saved!');
      setShowSettings(false);
      
    } catch (err) {
      console.error('Failed to save settings', err);
      toast.error('Failed to save settings');
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-violet-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Leads</h1>
          <p className="text-sm text-muted-foreground mt-1">Share your link to capture leads automatically</p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => setShowSettings(!showSettings)}
        >
          <Settings className="w-4 h-4 mr-2" />
          Settings
        </Button>
      </div>

      {/* Settings Panel (Collapsible) */}
      {showSettings && (
        <Card className="border-violet-200 bg-violet-50/50">
          <CardHeader>
            <CardTitle className="text-lg">Customize Your Lead Page</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Headline</Label>
              <Input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="Get Your Free Home Value Report"
              />
            </div>
            <div>
              <Label>Subheadline</Label>
              <Input
                value={subheadline}
                onChange={(e) => setSubheadline(e.target.value)}
                placeholder="Find out what your home is worth..."
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
            <TrendingUp className="w-5 h-5 text-violet-600" />
            Your Shareable Lead Page
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            {/* URL Section */}
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">
                Your Unique URL
              </Label>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-100 px-4 py-3 rounded-lg font-mono text-sm truncate">
                  {settings?.url || 'Loading...'}
                </div>
                <Button variant="outline" size="icon" onClick={copyUrl} title="Copy URL">
                  <Copy className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={shareUrl} title="Share">
                  <Share2 className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="icon" asChild title="Open in new tab">
                  <a href={settings?.url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Share this link on business cards, social media, email signatures, yard signs, etc.
              </p>
            </div>

            {/* QR Code Section */}
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-2 block">
                Your QR Code
              </Label>
              <div className="flex items-center gap-4">
                <div className="bg-white border rounded-xl p-3">
                  {settings?.qr_code_url ? (
                    <img 
                      src={settings.qr_code_url} 
                      alt="QR Code"
                      className="w-24 h-24"
                    />
                  ) : (
                    <div className="w-24 h-24 bg-gray-100 rounded flex items-center justify-center">
                      <QrCode className="w-8 h-8 text-gray-400" />
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
          <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t">
            <StatBox 
              label="Page Visits" 
              value={settings?.visits || 0} 
              icon={<Eye className="w-4 h-4" />}
            />
            <StatBox 
              label="Leads Captured" 
              value={stats.totalLeads} 
              icon={<FileText className="w-4 h-4" />}
            />
            <StatBox 
              label="Hot Leads" 
              value={stats.hotLeads}
              icon={<Flame className="w-4 h-4" />}
              highlight
            />
            <StatBox 
              label="Contact Rate" 
              value={`${stats.conversionRate}%`}
              icon={<TrendingUp className="w-4 h-4" />}
            />
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
                className={filter === 'hot' ? 'bg-orange-500 hover:bg-orange-600' : ''}
              >
                <Flame className="w-3 h-3 mr-1" />
                Hot ({stats.hotLeads})
              </Button>
              <Button 
                variant={filter === 'contacted' ? 'default' : 'outline'} 
                size="sm"
                onClick={() => setFilter('contacted')}
                className={filter === 'contacted' ? 'bg-green-500 hover:bg-green-600' : ''}
              >
                <CheckCircle className="w-3 h-3 mr-1" />
                Contacted ({stats.contactedLeads})
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredLeads.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
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


function StatBox({ label, value, icon, highlight }: { 
  label: string; 
  value: string | number; 
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className={`text-center p-4 rounded-xl ${highlight ? 'bg-orange-50' : 'bg-gray-50'}`}>
      <div className={`flex justify-center mb-2 ${highlight ? 'text-orange-600' : 'text-gray-500'}`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}


function LeadRow({ lead }: { lead: ConsumerLead }) {
  const isHot = lead.view_count > 1 || lead.agent_contact_clicked;
  
  return (
    <div className={`p-4 rounded-xl border ${isHot ? 'border-orange-200 bg-orange-50' : 'bg-gray-50'}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-gray-900 truncate">
              {lead.property_address}
            </p>
            {isHot && (
              <Badge className="bg-orange-500 text-white">
                <Flame className="w-3 h-3 mr-1" />
                Hot
              </Badge>
            )}
          </div>
          <p className="text-sm text-gray-500">
            {lead.property_city}, {lead.property_state} {lead.property_zip}
          </p>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
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
            <Badge className="bg-green-100 text-green-700">
              <CheckCircle className="w-3 h-3 mr-1" />
              Contacted
            </Badge>
          )}
          {lead.pdf_downloaded && (
            <Badge variant="outline" className="border-violet-300 text-violet-700">
              <FileText className="w-3 h-3 mr-1" />
              PDF
            </Badge>
          )}
          <a 
            href={`tel:${lead.consumer_phone}`}
            className="p-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors"
          >
            <Phone className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
}

