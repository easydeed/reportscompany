"use client";

import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, ArrowRight, BarChart3, Mail, Shield } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="flex min-h-screen">
      {/* Left — Form panel */}
      <div className="flex flex-1 flex-col justify-center px-6 py-12 lg:px-16 xl:px-24">
        <div className="mx-auto w-full max-w-md">
          {/* Logo */}
          <Link href="/" className="text-2xl font-bold text-[#6366F1]">
            TrendyReports
          </Link>

          <h1 className="mt-10 text-3xl font-bold tracking-tight text-foreground">
            Welcome back
          </h1>
          <p className="mt-2 text-muted-foreground">
            Sign in to your account to continue creating beautiful market
            reports.
          </p>

          {/* Google button */}
          <button
            type="button"
            className="mt-8 flex w-full items-center justify-center gap-3 rounded-lg border border-border bg-background px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-[#F8FAFC]"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1Z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23Z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62Z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53Z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </button>

          {/* Divider */}
          <div className="relative mt-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-background px-4 text-muted-foreground">
                or sign in with email
              </span>
            </div>
          </div>

          {/* Form */}
          <form className="mt-8 space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@company.com"
                className="h-12 rounded-lg"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="#"
                  className="text-sm font-medium text-[#6366F1] hover:text-[#4F46E5]"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  className="h-12 rounded-lg pr-12"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox id="remember" />
              <Label htmlFor="remember" className="text-sm font-normal text-muted-foreground">
                Keep me signed in
              </Label>
            </div>

            <button
              type="submit"
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#6366F1] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5]"
            >
              Sign in
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-muted-foreground">
            {"Don't have an account? "}
            <Link
              href="/register"
              className="font-semibold text-[#6366F1] hover:text-[#4F46E5]"
            >
              Start your free trial
            </Link>
          </p>
        </div>
      </div>

      {/* Right — Branded visual panel */}
      <div className="hidden flex-1 flex-col justify-between bg-[#1E293B] p-12 lg:flex xl:p-16">
        <div>
          <p className="text-sm font-medium uppercase tracking-widest text-[#818CF8]">
            Trusted by 2,000+ agents
          </p>
          <h2 className="mt-6 text-balance text-4xl font-bold leading-tight text-white">
            Market reports that
            <br />
            close deals faster.
          </h2>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-6">
          <div className="rounded-xl bg-white/5 p-5 backdrop-blur">
            <BarChart3 className="h-6 w-6 text-[#818CF8]" />
            <p className="mt-3 text-2xl font-bold text-white">8</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Report types</p>
          </div>
          <div className="rounded-xl bg-white/5 p-5 backdrop-blur">
            <Mail className="h-6 w-6 text-[#818CF8]" />
            <p className="mt-3 text-2xl font-bold text-white">50K+</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Emails sent monthly</p>
          </div>
          <div className="rounded-xl bg-white/5 p-5 backdrop-blur">
            <Shield className="h-6 w-6 text-[#818CF8]" />
            <p className="mt-3 text-2xl font-bold text-white">99.9%</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Uptime SLA</p>
          </div>
        </div>

        {/* Testimonial */}
        <div>
          <blockquote className="rounded-xl bg-white/5 p-6 backdrop-blur">
            <p className="leading-relaxed text-[#E2E8F0]">
              {
                '"TrendyReports transformed how I communicate with clients. The automated market reports save me 5+ hours every week and my clients love them."'
              }
            </p>
            <footer className="mt-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#6366F1] text-sm font-bold text-white">
                SJ
              </div>
              <div>
                <p className="text-sm font-semibold text-white">
                  Sarah Johnson
                </p>
                <p className="text-sm text-[#94A3B8]">
                  Top Producer, Compass Austin
                </p>
              </div>
            </footer>
          </blockquote>
        </div>
      </div>
    </div>
  );
}
