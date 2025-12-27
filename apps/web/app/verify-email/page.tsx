"use client";

import * as React from "react";
import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Logo } from "@/components/logo";
import { CheckCircle, AlertCircle, Loader2, Mail } from "lucide-react";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error" | "no-token">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("no-token");
      return;
    }

    verifyEmail();
  }, [token]);

  async function verifyEmail() {
    try {
      const res = await fetch("/api/proxy/v1/auth/verify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setStatus("success");
        setMessage(data.message || "Email verified successfully!");
        // Redirect to app after 3 seconds
        setTimeout(() => router.push("/app"), 3000);
      } else {
        setStatus("error");
        setMessage(data.detail || "Verification failed. Please try again.");
      }
    } catch (err) {
      setStatus("error");
      setMessage("Something went wrong. Please try again.");
    }
  }

  if (status === "loading") {
    return (
      <div className="text-center space-y-4">
        <Loader2 className="w-12 h-12 text-purple-600 animate-spin mx-auto" />
        <h2 className="text-xl font-semibold text-slate-900">Verifying your email...</h2>
        <p className="text-slate-600">Please wait a moment.</p>
      </div>
    );
  }

  if (status === "no-token") {
    return (
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto">
          <Mail className="w-8 h-8 text-yellow-600" />
        </div>
        <h2 className="text-2xl font-display font-semibold text-slate-900">
          No verification token
        </h2>
        <p className="text-slate-600">
          This link appears to be invalid. Please check your email for the correct link.
        </p>
        <div className="pt-4 space-x-4">
          <Link href="/login">
            <Button variant="outline">Go to Login</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-display font-semibold text-slate-900">
          Email Verified! 🎉
        </h2>
        <p className="text-slate-600">{message}</p>
        <p className="text-sm text-slate-500">Redirecting to your dashboard...</p>
        <div className="pt-4">
          <Link href="/app">
            <Button className="bg-gradient-to-r from-purple-600 to-purple-700">
              Go to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // Error state
  return (
    <div className="text-center space-y-4">
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
        <AlertCircle className="w-8 h-8 text-red-600" />
      </div>
      <h2 className="text-2xl font-display font-semibold text-slate-900">
        Verification Failed
      </h2>
      <p className="text-slate-600">{message}</p>
      <div className="pt-4 space-x-4">
        <Link href="/login">
          <Button variant="outline">Go to Login</Button>
        </Link>
        <Link href="/app">
          <Button className="bg-gradient-to-r from-purple-600 to-purple-700">
            Go to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <Logo variant="full" className="h-10 mx-auto" />
          </Link>
        </div>

        <Card className="p-8 shadow-xl border-slate-200 bg-white">
          <Suspense
            fallback={
              <div className="text-center py-8">
                <Loader2 className="w-8 h-8 text-purple-600 animate-spin mx-auto" />
                <p className="mt-4 text-slate-600">Loading...</p>
              </div>
            }
          >
            <VerifyEmailContent />
          </Suspense>
        </Card>
      </div>
    </div>
  );
}

