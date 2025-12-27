"use client";

import * as React from "react";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Logo } from "@/components/logo";
import { ArrowRight, Mail, Lock, Check, AlertCircle } from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const nextPath = searchParams.get("next") || "/app";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Use proxy route to ensure Set-Cookie works (same-origin)
      const res = await fetch("/api/proxy/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include", // Allow browser to accept Set-Cookie
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data?.detail || data?.message || "Invalid email or password");
        setLoading(false);
        return;
      }

      // Backend sets mr_token cookie via Set-Cookie header
      // Redirect to next path or dashboard
      router.push(nextPath);
    } catch (err: any) {
      console.error("Login failed", err);
      setError("Something went wrong. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 items-center">
        {/* Left side - Branding & Benefits */}
        <div className="hidden lg:block space-y-8">
          <Link href="/" className="inline-block group">
            <Logo variant="full" className="h-12 transition-transform group-hover:scale-105" />
          </Link>

          <div className="space-y-4">
            <h1 className="text-4xl font-display font-semibold text-slate-900 leading-tight">
              Beautiful market reports.
              <br />
              <span className="bg-gradient-to-r from-purple-600 to-purple-700 bg-clip-text text-transparent">
                Zero effort.
              </span>
            </h1>
            <p className="text-lg text-slate-600">
              Join 1,200+ real estate professionals who save 3+ hours every week
            </p>
          </div>

          <div className="space-y-4">
            {[
              "Instant MLS data sync",
              "Your brand on every report",
              "Automated delivery schedules",
              "Print-perfect PDFs in seconds",
            ].map((benefit, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <div className="h-6 w-6 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                  <Check className="h-4 w-4 text-purple-600" />
                </div>
                <span className="text-slate-700">{benefit}</span>
              </div>
            ))}
          </div>

          <div className="pt-8 border-t border-slate-200">
            <Link
              href="/"
              className="inline-flex items-center text-sm text-slate-500 hover:text-slate-900 transition-colors"
            >
              ← Back to home
            </Link>
          </div>
        </div>

        {/* Right side - Auth Form */}
        <Card className="w-full max-w-md mx-auto p-8 shadow-xl border-slate-200 bg-white">
          <div className="lg:hidden mb-6 text-center">
            <Link href="/" className="inline-block">
              <Logo variant="full" className="h-10 mx-auto" />
            </Link>
          </div>

          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-display font-semibold text-slate-900">Welcome back</h2>
              <p className="text-sm text-slate-600">Sign in to your TrendyReports account</p>
            </div>

            {/* Error Display */}
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-3 flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-900">Login failed</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}

            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-700">
                  Email
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

              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-700">
                  Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="h-11 pl-10"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 text-slate-600 cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                    disabled={loading}
                  />
                  Remember me
                </label>
                <Link href="/forgot-password" className="text-purple-600 hover:text-purple-700 font-medium">
                  Forgot password?
                </Link>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-11 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-medium shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Signing in..." : "Sign In"}
                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
              </Button>
            </form>

            {/* Sign up link */}
            <div className="pt-4 border-t border-slate-200 text-center">
              <p className="text-sm text-slate-600">
                Don&apos;t have an account?{" "}
                <Link href="/register" className="text-purple-600 hover:text-purple-700 font-medium">
                  Create one for free
                </Link>
              </p>
            </div>

            {/* Mobile: Back to home link */}
            <div className="lg:hidden pt-2 text-center">
              <Link
                href="/"
                className="inline-flex items-center text-sm text-slate-500 hover:text-slate-900 transition-colors"
              >
                ← Back to home
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-purple-50 flex items-center justify-center">
          <div className="text-slate-600">Loading...</div>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
