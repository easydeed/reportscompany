"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle, AlertCircle, RefreshCw } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const SUPPORT_EMAIL = "support@trendyreports.io";

/**
 * Landing page for the unsubscribe link in scheduled report emails.
 *
 * Every outcome lands here. The person reading this is a recipient on someone's
 * mailing list, not a TrendyReports account holder — so the copy never assumes
 * they can log in, and a failure always gives them a way to reach a human.
 *
 * States are set by apps/web/app/api/v1/email/unsubscribe/route.ts:
 *   (none) | success  → confirmed
 *   invalid           → the token did not verify (HTTP 400 from the API)
 *   error             → the request could not be completed (5xx / network)
 */
function UnsubscribedContent() {
  const searchParams = useSearchParams();
  const status = searchParams.get("status");
  const state =
    status === "invalid" || status === "error" ? status : "success";

  if (state === "success") {
    return (
      <Card
        icon={<CheckCircle className="w-8 h-8 text-green-600" />}
        iconBg="bg-green-100 dark:bg-green-900/30"
        title="You've been unsubscribed"
      >
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          You will no longer receive scheduled reports from this sender. It can
          take a few minutes for the change to take effect, so you may still see
          a message that was already on its way.
        </p>
        <div className="space-y-3">
          <Link href="/">
            <Button variant="default" className="w-full">
              Return to homepage
            </Button>
          </Link>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Still receiving emails after a day? Reply to the message you
            received, or contact{" "}
            <a
              href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(
                "Still receiving emails after unsubscribing"
              )}`}
              className="text-primary hover:underline"
            >
              {SUPPORT_EMAIL}
            </a>
            .
          </p>
        </div>
      </Card>
    );
  }

  if (state === "invalid") {
    return (
      <Card
        icon={<AlertCircle className="w-8 h-8 text-amber-600" />}
        iconBg="bg-amber-100 dark:bg-amber-900/30"
        title="We couldn't verify this link"
      >
        <p className="text-slate-600 dark:text-slate-400 mb-4">
          You have <strong>not</strong> been unsubscribed. The link may have
          been altered on its way to you — some email apps and security scanners
          rewrite links — or it may be from a very old message.
        </p>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          You can still opt out. Either reply to the email you received and ask
          to be removed, or send us the sender&apos;s name and we&apos;ll take
          care of it.
        </p>
        <div className="space-y-3">
          <a
            href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(
              "Please unsubscribe me"
            )}&body=${encodeURIComponent(
              "I clicked an unsubscribe link and it could not be verified. Please remove my address from this sender's list.\n\nSender (from the email):\n"
            )}`}
          >
            <Button variant="default" className="w-full">
              Email {SUPPORT_EMAIL}
            </Button>
          </a>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            We answer every request to be removed, whether or not the link
            worked.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card
      icon={<RefreshCw className="w-8 h-8 text-slate-600" />}
      iconBg="bg-slate-100 dark:bg-slate-700"
      title="Something went wrong"
    >
      <p className="text-slate-600 dark:text-slate-400 mb-4">
        You have <strong>not</strong> been unsubscribed. We couldn&apos;t
        complete the request just now — this is usually temporary.
      </p>
      <p className="text-slate-600 dark:text-slate-400 mb-6">
        Please try the link in your email again in a few minutes. If it still
        doesn&apos;t work, contact us and we&apos;ll remove you manually.
      </p>
      <div className="space-y-3">
        <a
          href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(
            "Please unsubscribe me"
          )}`}
        >
          <Button variant="default" className="w-full">
            Email {SUPPORT_EMAIL}
          </Button>
        </a>
      </div>
    </Card>
  );
}

function Card({
  icon,
  iconBg,
  title,
  children,
}: {
  icon: React.ReactNode;
  iconBg: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 text-center">
      <div
        className={`w-16 h-16 ${iconBg} rounded-full flex items-center justify-center mx-auto mb-6`}
      >
        {icon}
      </div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
        {title}
      </h1>
      {children}
    </div>
  );
}

export default function UnsubscribedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-md w-full mx-4">
        <Suspense
          fallback={
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 text-center">
              <p className="text-slate-500 dark:text-slate-400">Loading…</p>
            </div>
          }
        >
          <UnsubscribedContent />
        </Suspense>
        <p className="text-center text-sm text-slate-500 mt-6">
          © {new Date().getFullYear()} TrendyReports. All rights reserved.
        </p>
      </div>
    </div>
  );
}
