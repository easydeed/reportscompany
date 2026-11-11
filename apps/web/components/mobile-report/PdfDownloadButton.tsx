'use client';

import { useEffect, useRef, useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { PDF_COPY, pdfOpenHref, requestPdf, type PdfState } from '@/lib/pdf-download';

/**
 * The homeowner's PDF button (LR-022, D-380): every outcome is shown, with
 * something to do.
 *
 * - The request is bounded (lib/pdf-download) and aborted when the page goes
 *   away; a cancelled request that finds the button still mounted (an effect
 *   re-run) returns it to idle instead of leaving it on "Preparing".
 * - Once ready, "Open your PDF report" points at the open route, which signs a
 *   new link on every click, so a page left open never offers a dead link.
 */
export function PdfDownloadButton({
  reportId,
  fetchFn,
  openWindow = (url) => window.open(url, '_blank'),
}: {
  reportId: string;
  fetchFn?: (input: string, init?: RequestInit) => Promise<Response>;
  openWindow?: (url: string) => void;
}) {
  const [state, setState] = useState<PdfState>({ status: 'idle' });
  const run = useRef<AbortController | null>(null);
  const mounted = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      run.current?.abort();
    };
  }, []);

  const start = async () => {
    if (state.status === 'loading') return;
    run.current?.abort();
    const mine = new AbortController();
    run.current = mine;
    setState({ status: 'loading' });
    const result = await requestPdf(reportId, { fetchFn, signal: mine.signal });
    if (run.current !== mine) return;
    run.current = null;
    if (!mounted.current) return;
    if (!result) {
      setState({ status: 'idle' });
      return;
    }
    setState(result);
    if (result.status === 'ready' && result.url) openWindow(result.url);
  };

  return (
    <div className="pt-4 border-t" aria-live="polite">
      {state.status === 'ready' ? (
        <a
          href={pdfOpenHref(reportId)}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 w-full py-3 font-semibold transition"
          style={{ color: 'var(--primary-ink)' }}
        >
          <Download className="w-5 h-5" />
          Open your PDF report
        </a>
      ) : (
        <button
          onClick={start}
          disabled={state.status === 'loading'}
          className="flex items-center justify-center gap-2 w-full py-3 text-gray-600 hover:text-gray-900 transition"
        >
          {state.status === 'loading' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Download className="w-5 h-5" />
          )}
          {state.status === 'loading'
            ? PDF_COPY.loading
            : state.status === 'failed' || state.status === 'expired'
              ? 'Try again'
              : 'Download Full PDF Report'}
        </button>
      )}
      {(state.status === 'failed' || state.status === 'expired') && state.message && (
        <p className="text-center text-sm text-gray-600 mt-1" role="status">{state.message}</p>
      )}
    </div>
  );
}
