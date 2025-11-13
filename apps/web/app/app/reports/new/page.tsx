"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Wizard from "@/components/Wizard";
import { API_BASE, DEMO_ACC } from "@/lib/api";

export default function NewReportPage() {
  const router = useRouter();
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [links, setLinks] = useState<{html_url?: string; pdf_url?: string; json_url?: string}>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (payload: any) => {
    setIsSubmitting(true);
    setRunId(null);
    setStatus("pending");
    setLinks({});

    try {
      const res = await fetch(`${API_BASE}/v1/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Demo-Account": DEMO_ACC },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const json = await res.json();
      const id = json.report_id;
      setRunId(id);

      // Poll for completion
      let tries = 0;
      const poll = async () => {
        tries++;
        const r = await fetch(`${API_BASE}/v1/reports/${id}`, {
          headers: { "X-Demo-Account": DEMO_ACC },
        });
        const j = await r.json();
        setStatus(j.status);
        
        if (j.status === "completed") {
          setLinks({ html_url: j.html_url, pdf_url: j.pdf_url, json_url: j.json_url });
          setIsSubmitting(false);
        } else if (j.status === "failed" || tries > 60) {
          setIsSubmitting(false);
        } else {
          setTimeout(poll, 1000);
        }
      };
      poll();
    } catch (error) {
      console.error("Error creating report:", error);
      setStatus("failed");
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.push("/app/reports");
  };

  // Show wizard if no report is being generated
  if (!runId) {
    return <Wizard onSubmit={handleSubmit} onCancel={handleCancel} />;
  }

  // Show status/result
  return (
    <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">Report Generation</h1>
        
        <div className="bg-white rounded-lg border p-6 space-y-4">
          <div>
            <div className="text-sm text-slate-600">Run ID</div>
            <code className="text-sm font-mono">{runId}</code>
          </div>

          <div>
            <div className="text-sm text-slate-600">Status</div>
            <div className="mt-1">
              {status === "pending" && <span className="text-amber-600">⏳ Pending...</span>}
              {status === "processing" && <span className="text-blue-600">🔄 Processing...</span>}
              {status === "completed" && <span className="text-green-600">✅ Completed!</span>}
              {status === "failed" && <span className="text-red-600">❌ Failed</span>}
            </div>
          </div>

          {status === "completed" && links.html_url && (
            <div className="pt-4 border-t space-y-3">
              <div className="text-sm font-medium">Report Links:</div>
              <div className="flex gap-3">
                {links.pdf_url && (
                  <a
                    href={links.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    📄 Open PDF
                  </a>
                )}
                {links.html_url && (
                  <a
                    href={links.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    🌐 Open HTML
                  </a>
                )}
              </div>
            </div>
          )}

          <div className="pt-4 border-t">
            <button
              onClick={() => {
                setRunId(null);
                setStatus(null);
                setLinks({});
              }}
              className="text-blue-600 hover:underline text-sm"
            >
              ← Create Another Report
            </button>
          </div>
        </div>
      </div>
  );
}
