'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle2, Download, ArrowLeft, Loader2 } from 'lucide-react';
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
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';

type ParsedRow = {
  row: number;
  name: string;
  email: string;
  city: string;
  phone: string;
  status: 'ready' | 'error';
  reason?: string;
};

type BulkInviteResult = {
  total_rows: number;
  invited: number;
  skipped: number;
  errors: { row: number; email: string; reason: string }[];
};

type Step = 'upload' | 'preview' | 'results';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function parseCSV(text: string): ParsedRow[] {
  const lines = text.split(/\r?\n/).filter((l) => l.trim());
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
  const nameIdx = headers.indexOf('name');
  const emailIdx = headers.indexOf('email');
  const cityIdx = headers.indexOf('city');
  const phoneIdx = headers.indexOf('phone');

  if (emailIdx === -1) return [];

  const rows: ParsedRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',').map((c) => c.trim());
    const email = cols[emailIdx] || '';
    const name = nameIdx >= 0 ? cols[nameIdx] || '' : '';
    const city = cityIdx >= 0 ? cols[cityIdx] || '' : '';
    const phone = phoneIdx >= 0 ? cols[phoneIdx] || '' : '';

    let status: 'ready' | 'error' = 'ready';
    let reason: string | undefined;

    if (!email) {
      status = 'error';
      reason = 'Email is required';
    } else if (!EMAIL_RE.test(email)) {
      status = 'error';
      reason = 'Invalid email format';
    } else if (!name) {
      status = 'error';
      reason = 'Name is required';
    }

    rows.push({ row: i + 1, name, email, city, phone, status, reason });
  }
  return rows;
}

export function BulkInviteModal() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
  const [result, setResult] = useState<BulkInviteResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const readyCount = parsedRows.filter((r) => r.status === 'ready').length;
  const errorCount = parsedRows.filter((r) => r.status === 'error').length;

  function reset() {
    setStep('upload');
    setFile(null);
    setParsedRows([]);
    setResult(null);
    setIsSubmitting(false);
    setIsDragging(false);
  }

  function handleClose() {
    setOpen(false);
    setTimeout(reset, 200);
  }

  const processFile = useCallback(async (f: File) => {
    setFile(f);
    const text = await f.text();
    const rows = parseCSV(text);
    setParsedRows(rows);
    if (rows.length > 0) {
      setStep('preview');
    } else {
      toast({
        title: 'Invalid CSV',
        description: 'Could not parse any rows. Ensure the file has "name" and "email" columns.',
        variant: 'destructive',
      });
    }
  }, [toast]);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && (f.type === 'text/csv' || f.name.endsWith('.csv'))) {
      processFile(f);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) processFile(f);
  }

  async function handleSubmit() {
    if (!file) return;
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/proxy/v1/affiliate/bulk-invite', {
        method: 'POST',
        body: formData,
      });

      const data: BulkInviteResult = await response.json();

      if (!response.ok) {
        throw new Error((data as any).detail || (data as any).error || 'Bulk invite failed');
      }

      setResult(data);
      setStep('results');
      toast({
        title: 'Invitations sent!',
        description: `${data.invited} agent${data.invited !== 1 ? 's' : ''} invited successfully.`,
      });
    } catch (error) {
      console.error('Bulk invite failed:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to process bulk invite',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleClose(); else setOpen(true); }}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Upload className="h-4 w-4 mr-2" />
          Bulk Import
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[680px] max-h-[85vh] flex flex-col">
        {step === 'upload' && (
          <>
            <DialogHeader>
              <DialogTitle>Bulk Invite Agents</DialogTitle>
              <DialogDescription>
                Upload a CSV file to invite multiple agents at once.
              </DialogDescription>
            </DialogHeader>

            <div className="py-4 space-y-4">
              <div
                className={`
                  border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
                  ${isDragging
                    ? 'border-primary bg-primary/5'
                    : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30'
                  }
                `}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <FileSpreadsheet className="h-10 w-10 mx-auto text-muted-foreground/60 mb-3" />
                <p className="text-sm font-medium text-foreground mb-1">
                  Drop your CSV here or click to browse
                </p>
                <p className="text-xs text-muted-foreground">
                  Columns: name, email, city, phone, job_title, company_name, license_number
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={handleFileSelect}
                />
              </div>

              <a
                href="/sample-agent-invite.csv"
                download
                className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
              >
                <Download className="h-3.5 w-3.5" />
                Download sample CSV
              </a>
            </div>
          </>
        )}

        {step === 'preview' && (
          <>
            <DialogHeader>
              <DialogTitle>Preview Import</DialogTitle>
              <DialogDescription>
                {readyCount > 0 && (
                  <span className="text-green-600 font-medium">{readyCount} agent{readyCount !== 1 ? 's' : ''} ready to invite</span>
                )}
                {readyCount > 0 && errorCount > 0 && ', '}
                {errorCount > 0 && (
                  <span className="text-destructive font-medium">{errorCount} with errors</span>
                )}
              </DialogDescription>
            </DialogHeader>

            <div className="flex-1 overflow-auto min-h-0 -mx-6 px-6">
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/40">
                      <th className="text-left py-2 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">#</th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Name</th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email</th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">City</th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {parsedRows.map((row) => (
                      <tr
                        key={row.row}
                        className={row.status === 'error' ? 'bg-destructive/5' : 'hover:bg-muted/30'}
                      >
                        <td className="py-2 px-3 text-muted-foreground tabular-nums">{row.row}</td>
                        <td className="py-2 px-3 font-medium">{row.name || '—'}</td>
                        <td className="py-2 px-3 text-muted-foreground">{row.email || '—'}</td>
                        <td className="py-2 px-3 text-muted-foreground">{row.city || '—'}</td>
                        <td className="py-2 px-3">
                          {row.status === 'ready' ? (
                            <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
                              Ready
                            </Badge>
                          ) : (
                            <Badge variant="destructive" className="font-normal">
                              {row.reason}
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0">
              <Button variant="outline" onClick={() => { setStep('upload'); setFile(null); setParsedRows([]); }}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <Button onClick={handleSubmit} disabled={isSubmitting || readyCount === 0}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  `Send ${readyCount} Invitation${readyCount !== 1 ? 's' : ''}`
                )}
              </Button>
            </DialogFooter>
          </>
        )}

        {step === 'results' && result && (
          <>
            <DialogHeader>
              <DialogTitle>Import Complete</DialogTitle>
            </DialogHeader>

            <div className="py-4 space-y-4">
              <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-green-800">
                    {result.invited} invitation{result.invited !== 1 ? 's' : ''} sent
                  </p>
                  {result.skipped > 0 && (
                    <p className="text-xs text-green-700 mt-0.5">
                      {result.skipped} row{result.skipped !== 1 ? 's' : ''} skipped
                    </p>
                  )}
                </div>
              </div>

              {result.errors.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                    <AlertCircle className="h-4 w-4" />
                    Skipped rows
                  </p>
                  <div className="border rounded-lg overflow-hidden max-h-48 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-muted/40">
                          <th className="text-left py-1.5 px-3 text-xs font-semibold text-muted-foreground">Row</th>
                          <th className="text-left py-1.5 px-3 text-xs font-semibold text-muted-foreground">Email</th>
                          <th className="text-left py-1.5 px-3 text-xs font-semibold text-muted-foreground">Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {result.errors.map((err, i) => (
                          <tr key={i} className="bg-destructive/5">
                            <td className="py-1.5 px-3 tabular-nums">{err.row}</td>
                            <td className="py-1.5 px-3 text-muted-foreground">{err.email || '—'}</td>
                            <td className="py-1.5 px-3 text-destructive">{err.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
