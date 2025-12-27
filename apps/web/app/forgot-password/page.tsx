"use client";

import * as React from "react";
import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Logo } from "@/components/logo";
import { Mail, ArrowLeft, CheckCircle, AlertCircle } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/proxy/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data?.detail || "Something went wrong. Please try again.");
        setLoading(false);
        return;
      }

      setSuccess(true);
    } catch (err) {
      console.error("Forgot password error:", err);
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <Logo variant="full" className="h-10 mx-auto" />
          </Link>
        </div>

        <Card className="p-8 shadow-xl border-slate-200 bg-white">
          {success ? (
            // Success State
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-display font-semibold text-slate-900">
                Check your email
              </h2>
              <p className="text-slate-600">
                If an account exists for <strong>{email}</strong>, you'll receive a password reset link shortly.
              </p>
              <p className="text-sm text-slate-500">
                Didn't receive the email? Check your spam folder or{" "}
                <button
                  onClick={() => {
                    setSuccess(false);
                    setEmail("");
                  }}
                  className="text-purple-600 hover:text-purple-700 font-medium"
                >
                  try again
                </button>
              </p>
              <div className="pt-4">
                <Link
                  href="/login"
                  className="inline-flex items-center text-sm text-slate-500 hover:text-slate-900 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to login
                </Link>
              </div>
            </div>
          ) : (
            // Form State
            <div className="space-y-6">
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-display font-semibold text-slate-900">
                  Forgot your password?
                </h2>
                <p className="text-sm text-slate-600">
                  No problem! Enter your email and we'll send you a reset link.
                </p>
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-3 flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-slate-700">
                    Email address
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      autoComplete="email"
                      placeholder="you@company.com"
                      className="h-11 pl-10"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      disabled={loading}
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading || !email}
                  className="w-full h-11 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-medium shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Sending..." : "Send reset link"}
                </Button>
              </form>

              <div className="text-center pt-4 border-t border-slate-200">
                <Link
                  href="/login"
                  className="inline-flex items-center text-sm text-slate-500 hover:text-slate-900 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to login
                </Link>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

