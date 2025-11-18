"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Logo } from "@/components/logo";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { AlertCircle, Check } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/proxy/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name: fullName, email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(
          data?.detail ||
            data?.message ||
            "We couldn't create your account. Please check your details and try again."
        );
        setLoading(false);
        return;
      }

      // On success, take new agent straight into the app
      router.push("/app");
    } catch (err) {
      console.error("Register error", err);
      setError("Something went wrong. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-purple-50 flex flex-col items-center">
      {/* Top nav strip */}
      <div className="w-full max-w-5xl flex items-center justify-between px-4 pt-6 pb-4">
        <Link href="/" className="flex items-center gap-2 group">
          <Logo variant="full" className="h-7 w-auto transition-transform group-hover:scale-105" />
        </Link>
        <Link
          href="/login"
          className="text-sm text-slate-500 hover:text-slate-900 transition-colors"
        >
          Already have an account?{" "}
          <span className="font-medium text-slate-900">Sign in</span>
        </Link>
      </div>

      {/* Main content */}
      <div className="w-full max-w-5xl flex-1 flex flex-col md:flex-row items-center justify-center px-4 pb-10 gap-10">
        {/* Left side: benefits (hidden on small screens) */}
        <div className="hidden md:flex flex-1 flex-col gap-4">
          <p className="inline-flex items-center text-xs font-semibold uppercase tracking-wide text-purple-700/80">
            For busy real estate agents
          </p>
          <h1 className="text-3xl md:text-4xl font-display font-semibold text-slate-900">
            Create your free TrendyReports account.
          </h1>
          <p className="text-sm md:text-base text-slate-600 max-w-md">
            Set up your account in under a minute. We'll turn your MLS data into beautiful, branded
            market reports and listing galleries — so you can stay in front of your clients without
            burning your evenings on spreadsheets and design tools.
          </p>
          <ul className="mt-4 space-y-3">
            {[
              "Connect your market and start with the Free plan.",
              "Photo-rich PDFs and email-ready reports in seconds.",
              "Your name and logo on every report — we stay invisible.",
            ].map((benefit, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <div className="h-6 w-6 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Check className="h-4 w-4 text-purple-600" />
                </div>
                <span className="text-slate-700">{benefit}</span>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-slate-500">
            Industry affiliate (title, lender, brokerage)?{" "}
            <Link href="/#for-affiliates" className="text-purple-700 hover:underline">
              Book an affiliate demo instead.
            </Link>
          </p>
        </div>

        {/* Right side: registration form */}
        <div className="flex-1 max-w-md w-full">
          <Card className="shadow-xl border border-slate-200 bg-white">
            <CardHeader className="space-y-1">
              <CardTitle className="text-lg md:text-xl text-slate-900">
                Get started in less than a minute
              </CardTitle>
              <CardDescription className="text-sm text-slate-600">
                Create your TrendyReports account. No credit card required.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleSubmit}>
                {error && (
                  <div className="rounded-lg bg-red-50 border border-red-200 p-3 flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-900">Registration failed</p>
                      <p className="text-sm text-red-700 mt-1">{error}</p>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="fullName">Full name</Label>
                  <Input
                    id="fullName"
                    autoComplete="name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    disabled={loading}
                    placeholder="Jane Agent"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Work email</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={loading}
                    placeholder="you@example.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    minLength={8}
                  />
                  <p className="text-xs text-slate-500">
                    Use at least 8 characters. A mix of letters, numbers and symbols is best.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    disabled={loading}
                  />
                </div>

                <Button
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-medium shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  type="submit"
                  disabled={loading}
                >
                  {loading ? "Creating your account…" : "Create free account"}
                </Button>
              </form>

              <p className="mt-4 text-xs text-center text-slate-500">
                By creating an account, you agree to our{" "}
                <Link href="/terms" className="text-purple-700 hover:underline">
                  Terms
                </Link>{" "}
                and{" "}
                <Link href="/privacy" className="text-purple-700 hover:underline">
                  Privacy Policy
                </Link>
                .
              </p>
            </CardContent>
          </Card>

          {/* Mobile-only small note for affiliates */}
          <p className="mt-4 text-xs text-center text-slate-500 md:hidden">
            Industry affiliate?{" "}
            <Link href="/#for-affiliates" className="text-purple-700 hover:underline">
              Book an affiliate demo instead.
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
