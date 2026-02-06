'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { 
  Loader2, 
  Save, 
  Image as ImageIcon, 
  Palette, 
  User, 
  Globe, 
  FileText, 
  Mail,
  Download,
  Send,
  CheckCircle2,
  Info
} from 'lucide-react';

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

interface BrandingFormProps {
  initialData: BrandingData;
}

export function BrandingForm({ initialData }: BrandingFormProps) {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [formData, setFormData] = useState<BrandingData>(initialData);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/proxy/v1/affiliate/branding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to save branding');
      }

      toast({
        title: 'Branding saved',
        description: 'Your white-label branding has been updated successfully.',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save branding',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof BrandingData, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value || null,
    }));
  };

  const handleDownloadSamplePdf = async () => {
    setIsDownloadingPdf(true);
    try {
      const response = await fetch('/api/proxy/v1/branding/sample-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_type: 'market_snapshot' }),
      });
      
      if (!response.ok) throw new Error('Failed to generate PDF');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${formData.brand_display_name.replace(/\s+/g, '_')}_Sample_Report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({ title: 'PDF Downloaded', description: 'Sample report downloaded successfully.' });
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to download sample PDF', variant: 'destructive' });
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleSendTestEmail = async () => {
    setIsSendingEmail(true);
    try {
      const response = await fetch('/api/proxy/v1/branding/test-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (!response.ok) throw new Error('Failed to send test email');
      
      toast({ title: 'Test Email Sent', description: 'Check your inbox for the branded test email.' });
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to send test email', variant: 'destructive' });
    } finally {
      setIsSendingEmail(false);
    }
  };

  const primaryColor = formData.primary_color || '#4F46E5';
  const accentColor = formData.accent_color || '#F26B2B';

  return (
    <div className="space-y-8">
      <form onSubmit={handleSubmit}>
        {/* Brand Identity Section */}
        <Card className="mb-6">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <ImageIcon className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <CardTitle className="text-lg">Brand Identity</CardTitle>
                <CardDescription>Your company name and logos</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Brand Name */}
            <div className="space-y-2">
              <Label htmlFor="brand_display_name" className="text-sm font-medium">
                Brand Display Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="brand_display_name"
                value={formData.brand_display_name}
                onChange={(e) => handleChange('brand_display_name', e.target.value)}
                placeholder="Pacific Coast Title"
                className="max-w-md"
                required
              />
              <p className="text-xs text-muted-foreground">
                This name appears on all client-facing reports and emails
              </p>
            </div>

            {/* Logos Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Header Logo */}
              <div className="space-y-3 p-4 bg-muted/30 rounded-lg border border-dashed">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-md flex items-center justify-center text-white text-xs font-bold"
                       style={{ background: `linear-gradient(135deg, ${primaryColor}, ${accentColor})` }}>
                    H
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Header Logo</Label>
                    <p className="text-xs text-muted-foreground">For PDF header (on gradient)</p>
                  </div>
                </div>
                <Input
                  type="url"
                  value={formData.logo_url || ''}
                  onChange={(e) => handleChange('logo_url', e.target.value)}
                  placeholder="https://example.com/logo-white.png"
                  className="text-sm"
                />
                <div className="flex items-start gap-2 text-xs text-muted-foreground bg-indigo-50 p-2 rounded">
                  <Info className="h-3.5 w-3.5 mt-0.5 text-indigo-500 flex-shrink-0" />
                  <span>Use a <strong>white or light-colored</strong> logo version for best visibility on the gradient header</span>
                </div>
                {formData.logo_url && (
                  <div className="p-3 rounded-lg" style={{ background: `linear-gradient(135deg, ${primaryColor}, ${accentColor})` }}>
                    <img src={formData.logo_url} alt="Header preview" className="h-8 w-auto object-contain brightness-0 invert" 
                         onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                  </div>
                )}
              </div>

              {/* Footer Logo */}
              <div className="space-y-3 p-4 bg-muted/30 rounded-lg border border-dashed">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-md flex items-center justify-center bg-slate-200 text-slate-600 text-xs font-bold">
                    F
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Footer Logo</Label>
                    <p className="text-xs text-muted-foreground">For PDF footer (on gray)</p>
                  </div>
                </div>
                <Input
                  type="url"
                  value={formData.footer_logo_url || ''}
                  onChange={(e) => handleChange('footer_logo_url', e.target.value)}
                  placeholder="https://example.com/logo-color.png"
                  className="text-sm"
                />
                <div className="flex items-start gap-2 text-xs text-muted-foreground bg-slate-100 p-2 rounded">
                  <Info className="h-3.5 w-3.5 mt-0.5 text-slate-500 flex-shrink-0" />
                  <span>Use your <strong>full-color or dark</strong> logo version for visibility on the light gray footer</span>
                </div>
                {formData.footer_logo_url && (
                  <div className="p-3 rounded-lg bg-slate-100">
                    <img src={formData.footer_logo_url} alt="Footer preview" className="h-8 w-auto object-contain" 
                         onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Colors Section */}
        <Card className="mb-6">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Palette className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <CardTitle className="text-lg">Brand Colors</CardTitle>
                <CardDescription>Customize the look of your reports</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Primary Color */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">Primary Color</Label>
                <div className="flex gap-3">
                  <div className="relative">
                    <input
                      type="color"
                      value={primaryColor}
                      onChange={(e) => handleChange('primary_color', e.target.value)}
                      className="w-12 h-12 rounded-lg border-2 border-border cursor-pointer"
                    />
                  </div>
                  <div className="flex-1">
                    <Input
                      value={formData.primary_color || ''}
                      onChange={(e) => handleChange('primary_color', e.target.value)}
                      placeholder="#4F46E5"
                      maxLength={7}
                      className="font-mono"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Headers, ribbons, gradients</p>
                  </div>
                </div>
              </div>

              {/* Accent Color */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">Accent Color</Label>
                <div className="flex gap-3">
                  <div className="relative">
                    <input
                      type="color"
                      value={accentColor}
                      onChange={(e) => handleChange('accent_color', e.target.value)}
                      className="w-12 h-12 rounded-lg border-2 border-border cursor-pointer"
                    />
                  </div>
                  <div className="flex-1">
                    <Input
                      value={formData.accent_color || ''}
                      onChange={(e) => handleChange('accent_color', e.target.value)}
                      placeholder="#F26B2B"
                      maxLength={7}
                      className="font-mono"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Buttons, highlights, CTAs</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Color Preview */}
            <div className="mt-6 p-4 rounded-xl border">
              <p className="text-xs text-muted-foreground mb-3">Preview</p>
              <div className="h-16 rounded-lg overflow-hidden" 
                   style={{ background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)` }}>
                <div className="h-full flex items-center justify-between px-6">
                  <div className="text-white">
                    <div className="font-bold">{formData.brand_display_name}</div>
                    <div className="text-xs opacity-80">Market Intelligence</div>
                  </div>
                  {formData.logo_url && (
                    <img src={formData.logo_url} alt="" className="h-8 brightness-0 invert" 
                         onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact Information Section */}
        <Card className="mb-6">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <User className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-lg">Contact Information</CardTitle>
                <CardDescription>Your contact details shown on reports</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Rep Photo */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Representative Photo</Label>
                <Input
                  type="url"
                  value={formData.rep_photo_url || ''}
                  onChange={(e) => handleChange('rep_photo_url', e.target.value)}
                  placeholder="https://example.com/headshot.jpg"
                />
                <p className="text-xs text-muted-foreground">Circular headshot for footer</p>
              </div>

              {/* Website */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Website</Label>
                <div className="flex gap-2 items-center">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  <Input
                    type="url"
                    value={formData.website_url || ''}
                    onChange={(e) => handleChange('website_url', e.target.value)}
                    placeholder="https://example.com"
                    className="flex-1"
                  />
                </div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {/* Contact Line 1 */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Contact Line 1</Label>
                <Input
                  value={formData.contact_line1 || ''}
                  onChange={(e) => handleChange('contact_line1', e.target.value)}
                  placeholder="John Doe • Senior Title Rep"
                />
                <p className="text-xs text-muted-foreground">Name, title, or company</p>
              </div>

              {/* Contact Line 2 */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">Contact Line 2</Label>
                <Input
                  value={formData.contact_line2 || ''}
                  onChange={(e) => handleChange('contact_line2', e.target.value)}
                  placeholder="555-123-4567 • john@example.com"
                />
                <p className="text-xs text-muted-foreground">Phone, email, or additional info</p>
              </div>
            </div>

            {/* Contact Preview */}
            {(formData.rep_photo_url || formData.contact_line1 || formData.contact_line2) && (
              <div className="mt-4 p-4 bg-slate-50 rounded-lg border">
                <p className="text-xs text-muted-foreground mb-3">Footer Preview</p>
                <div className="flex items-center gap-4">
                  {formData.rep_photo_url && (
                    <img src={formData.rep_photo_url} alt="" 
                         className="w-12 h-12 rounded-full object-cover border-2 border-white shadow"
                         onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                  )}
                  <div className="flex-1">
                    {formData.contact_line1 && <div className="font-medium text-sm">{formData.contact_line1}</div>}
                    {formData.contact_line2 && <div className="text-xs text-muted-foreground">{formData.contact_line2}</div>}
                    {formData.website_url && <div className="text-xs text-blue-600">{formData.website_url}</div>}
                  </div>
                  {formData.footer_logo_url && (
                    <img src={formData.footer_logo_url} alt="" className="h-10 w-auto object-contain"
                         onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end mb-8">
          <Button type="submit" disabled={isSubmitting} size="lg" className="min-w-[200px]">
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Branding
              </>
            )}
          </Button>
        </div>
      </form>

      {/* Test & Preview Section */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <CardTitle className="text-lg">Test Your Branding</CardTitle>
              <CardDescription>Preview how your brand appears to clients</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {/* Sample PDF */}
            <div className="p-5 rounded-xl border-2 border-dashed hover:border-indigo-300 hover:bg-indigo-50/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-indigo-100 rounded-lg">
                  <FileText className="h-6 w-6 text-indigo-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Sample PDF Report</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Download a Market Snapshot PDF with your branding applied
                  </p>
                  <Button 
                    variant="outline" 
                    onClick={handleDownloadSamplePdf}
                    disabled={isDownloadingPdf}
                    className="w-full"
                  >
                    {isDownloadingPdf ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...</>
                    ) : (
                      <><Download className="mr-2 h-4 w-4" /> Download Sample PDF</>
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {/* Test Email */}
            <div className="p-5 rounded-xl border-2 border-dashed hover:border-orange-300 hover:bg-orange-50/50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-orange-100 rounded-lg">
                  <Mail className="h-6 w-6 text-orange-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Test Email</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Send a branded email to yourself to preview the look
                  </p>
                  <Button 
                    variant="outline" 
                    onClick={handleSendTestEmail}
                    disabled={isSendingEmail}
                    className="w-full"
                  >
                    {isSendingEmail ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending...</>
                    ) : (
                      <><Send className="mr-2 h-4 w-4" /> Send Test Email</>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Tip */}
          <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex gap-3">
              <Info className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-amber-800 mb-1">Pro Tip</p>
                <p className="text-amber-700">
                  Save your branding changes first before testing. The sample PDF and test email 
                  will use your most recently saved settings.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
