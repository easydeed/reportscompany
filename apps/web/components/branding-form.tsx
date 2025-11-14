'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Eye, Save } from 'lucide-react';

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

interface BrandingFormProps {
  initialData: BrandingData;
}

export function BrandingForm({ initialData }: BrandingFormProps) {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
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

  const primaryColor = formData.primary_color || '#7C3AED';
  const accentColor = formData.accent_color || '#F26B2B';

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle>Branding Configuration</CardTitle>
          <CardDescription>
            Define your brand identity for client-facing reports and emails
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Brand Display Name */}
            <div className="space-y-2">
              <Label htmlFor="brand_display_name">
                Brand Display Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="brand_display_name"
                value={formData.brand_display_name}
                onChange={(e) => handleChange('brand_display_name', e.target.value)}
                placeholder="Pacific Coast Title"
                required
              />
              <p className="text-xs text-muted-foreground">
                Your company name as shown to end clients
              </p>
            </div>

            {/* Logo URL */}
            <div className="space-y-2">
              <Label htmlFor="logo_url">Logo URL</Label>
              <Input
                id="logo_url"
                type="url"
                value={formData.logo_url || ''}
                onChange={(e) => handleChange('logo_url', e.target.value)}
                placeholder="https://example.com/logo.png"
              />
              <p className="text-xs text-muted-foreground">
                Direct link to your logo image (PNG or SVG recommended)
              </p>
            </div>

            {/* Colors */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="primary_color">Primary Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="primary_color"
                    value={formData.primary_color || ''}
                    onChange={(e) => handleChange('primary_color', e.target.value)}
                    placeholder="#7C3AED"
                    maxLength={7}
                  />
                  <div
                    className="w-12 h-10 rounded border border-border"
                    style={{ backgroundColor: primaryColor }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Headers, ribbons</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="accent_color">Accent Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="accent_color"
                    value={formData.accent_color || ''}
                    onChange={(e) => handleChange('accent_color', e.target.value)}
                    placeholder="#F26B2B"
                    maxLength={7}
                  />
                  <div
                    className="w-12 h-10 rounded border border-border"
                    style={{ backgroundColor: accentColor }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">Buttons, highlights</p>
              </div>
            </div>

            {/* Rep Photo */}
            <div className="space-y-2">
              <Label htmlFor="rep_photo_url">Representative Photo URL</Label>
              <Input
                id="rep_photo_url"
                type="url"
                value={formData.rep_photo_url || ''}
                onChange={(e) => handleChange('rep_photo_url', e.target.value)}
                placeholder="https://example.com/photo.jpg"
              />
              <p className="text-xs text-muted-foreground">
                Optional headshot for email personalization
              </p>
            </div>

            {/* Contact Lines */}
            <div className="space-y-2">
              <Label htmlFor="contact_line1">Contact Line 1</Label>
              <Input
                id="contact_line1"
                value={formData.contact_line1 || ''}
                onChange={(e) => handleChange('contact_line1', e.target.value)}
                placeholder="John Doe • Senior Title Representative"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="contact_line2">Contact Line 2</Label>
              <Input
                id="contact_line2"
                value={formData.contact_line2 || ''}
                onChange={(e) => handleChange('contact_line2', e.target.value)}
                placeholder="555-123-4567 • john@example.com"
              />
            </div>

            {/* Website */}
            <div className="space-y-2">
              <Label htmlFor="website_url">Website URL</Label>
              <Input
                id="website_url"
                type="url"
                value={formData.website_url || ''}
                onChange={(e) => handleChange('website_url', e.target.value)}
                placeholder="https://example.com"
              />
            </div>

            {/* Submit Button */}
            <Button type="submit" disabled={isSubmitting} className="w-full">
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
          </form>
        </CardContent>
      </Card>

      {/* Live Preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Live Preview</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </div>
          <CardDescription>
            How your brand will appear on client reports and emails
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Email Preview */}
            <div className="rounded-lg border border-border overflow-hidden">
              <div
                className="h-2"
                style={{
                  background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)`,
                }}
              />
              <div className="p-6 bg-background">
                <div className="flex items-center gap-4 mb-4">
                  {formData.logo_url ? (
                    <img
                      src={formData.logo_url}
                      alt={formData.brand_display_name}
                      className="h-12 w-auto object-contain"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div
                      className="h-12 w-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                      style={{ backgroundColor: primaryColor }}
                    >
                      {formData.brand_display_name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <div className="font-bold text-lg">{formData.brand_display_name}</div>
                    <div className="text-xs text-muted-foreground">Market Report</div>
                  </div>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="h-4 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-full" />
                  <div className="h-4 bg-muted rounded w-5/6" />
                </div>

                <button
                  className="w-full rounded-lg py-3 text-white font-semibold text-sm"
                  style={{ backgroundColor: accentColor }}
                  disabled
                >
                  View Full Report (PDF)
                </button>

                {(formData.contact_line1 || formData.contact_line2) && (
                  <div className="mt-4 pt-4 border-t border-border">
                    {formData.contact_line1 && (
                      <div className="text-xs text-muted-foreground">
                        {formData.contact_line1}
                      </div>
                    )}
                    {formData.contact_line2 && (
                      <div className="text-xs text-muted-foreground">
                        {formData.contact_line2}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* PDF Header Preview */}
            <div className="rounded-lg border border-border overflow-hidden">
              <div
                className="p-6 text-white"
                style={{
                  background: `linear-gradient(135deg, ${primaryColor} 0%, ${accentColor} 100%)`,
                }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-xl">{formData.brand_display_name}</div>
                    <div className="text-sm opacity-90">Market Intelligence</div>
                  </div>
                  {formData.logo_url && (
                    <img
                      src={formData.logo_url}
                      alt="Logo"
                      className="h-8 w-auto object-contain brightness-0 invert"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  )}
                </div>
              </div>
              <div className="p-6 bg-background">
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 rounded bg-muted">
                    <div className="text-xs text-muted-foreground">Median Price</div>
                    <div className="text-lg font-bold">$825K</div>
                  </div>
                  <div className="text-center p-3 rounded bg-muted">
                    <div className="text-xs text-muted-foreground">Closed Sales</div>
                    <div className="text-lg font-bold">23</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

