'use client';

import { useState } from 'react';
import { UserPlus, Copy, Check } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

interface InviteResponse {
  ok: boolean;
  account_id: string;
  user_id: string;
  token: string;
  invite_url: string;
}

export function InviteAgentModal() {
  const [open, setOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    default_city: '',
  });

  const [errors, setErrors] = useState({
    name: '',
    email: '',
  });

  function validateForm(): boolean {
    const newErrors = { name: '', email: '' };
    let isValid = true;

    if (!formData.name.trim()) {
      newErrors.name = 'Agent name is required';
      isValid = false;
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({ name: '', email: '' });

    try {
      const response = await fetch('/api/proxy/v1/affiliate/invite-agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          default_city: formData.default_city || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 400 && data.detail?.includes('email already exists')) {
          setErrors({ ...errors, email: 'A user with this email already exists' });
          return;
        }
        throw new Error(data.detail || data.error || 'Failed to send invitation');
      }

      const result: InviteResponse = data;

      // Show success and invite URL
      setInviteUrl(result.invite_url);
      
      toast({
        title: 'Invitation Sent!',
        description: `Successfully invited ${formData.email}`,
      });

      // Reset form
      setFormData({ name: '', email: '', default_city: '' });
    } catch (error) {
      console.error('Failed to invite agent:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to send invitation',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function copyToClipboard() {
    if (!inviteUrl) return;

    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopied(true);
      toast({
        title: 'Copied!',
        description: 'Invite URL copied to clipboard',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      });
    }
  }

  function handleClose() {
    setOpen(false);
    // Reset form and invite URL after a short delay (so the dialog close animation completes)
    setTimeout(() => {
      setFormData({ name: '', email: '', default_city: '' });
      setErrors({ name: '', email: '' });
      setInviteUrl(null);
      setCopied(false);
    }, 200);
  }

  return (
    <Dialog open={open} onOpenChange={(newOpen) => {
      if (!newOpen) {
        handleClose();
      } else {
        setOpen(true);
      }
    }}>
      <DialogTrigger asChild>
        <Button>
          <UserPlus className="h-4 w-4 mr-2" />
          Invite Agent
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Invite Sponsored Agent</DialogTitle>
          <DialogDescription>
            Create a new sponsored account for an agent. They'll receive an invitation email
            to set up their account.
          </DialogDescription>
        </DialogHeader>

        {inviteUrl ? (
          <div className="space-y-4 py-4">
            <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
              <Check className="h-5 w-5 text-green-500" />
              <p className="text-sm font-medium">Invitation sent successfully!</p>
            </div>

            <div className="space-y-2">
              <Label>Invitation URL</Label>
              <div className="flex gap-2">
                <Input value={inviteUrl} readOnly className="font-mono text-sm" />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={copyToClipboard}
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Share this URL with the agent to complete their onboarding
              </p>
            </div>

            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">
                  Agent/Company Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="name"
                  placeholder="John Doe Realty"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  disabled={isSubmitting}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">
                  Email Address <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="agent@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={isSubmitting}
                />
                {errors.email && (
                  <p className="text-sm text-destructive">{errors.email}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="city">Default City (Optional)</Label>
                <Input
                  id="city"
                  placeholder="La Verne"
                  value={formData.default_city}
                  onChange={(e) => setFormData({ ...formData, default_city: e.target.value })}
                  disabled={isSubmitting}
                />
                <p className="text-xs text-muted-foreground">
                  The agent's primary market area
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Sending...' : 'Send Invitation'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

