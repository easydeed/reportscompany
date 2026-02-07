"use client";

import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, ArrowRight, Check } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

const benefits = [
  "Unlimited market reports from live MLS data",
  "Branded email and PDF delivery on autopilot",
  "Lead capture pages with QR code integration",
  "Contact management with group segmentation",
  "8 report types — one click each",
];

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="flex min-h-screen">
      {/* Left — Branded visual panel */}
      <div className="hidden flex-1 flex-col justify-between bg-[#1E293B] p-12 lg:flex xl:p-16">
        <div>
          <Link href="/" className="text-2xl font-bold text-white">
            TrendyReports
          </Link>
          <h2 className="mt-12 text-balance text-4xl font-bold leading-tight text-white">
            Start creating beautiful
            <br />
            market reports today.
          </h2>
          <p className="mt-4 text-lg text-[#94A3B8]">
            14-day free trial. No credit card required.
          </p>
        </div>

        {/* Benefits */}
        <div className="space-y-5">
          {benefits.map((b) => (
            <div key={b} className="flex items-start gap-3">
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#6366F1]">
                <Check className="h-3.5 w-3.5 text-white" />
              </div>
              <p className="text-[#E2E8F0]">{b}</p>
            </div>
          ))}
        </div>

        {/* Social proof */}
        <div>
          <div className="flex items-center gap-1">
            {[...Array(5)].map((_, i) => (
              <svg
                key={i}
                className="h-5 w-5 text-[#818CF8]"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
            <span className="ml-2 text-sm font-medium text-[#94A3B8]">
              4.9/5 from 500+ agents
            </span>
          </div>
          <div className="mt-4 flex -space-x-3">
            {[
              "bg-[#6366F1]",
              "bg-[#4338CA]",
              "bg-[#818CF8]",
              "bg-[#475569]",
              "bg-[#334155]",
            ].map((color, i) => (
              <div
                key={i}
                className={`flex h-10 w-10 items-center justify-center rounded-full border-2 border-[#1E293B] text-xs font-bold text-white ${color}`}
              >
                {["SJ", "MC", "LP", "DR", "AW"][i]}
              </div>
            ))}
            <div className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-[#1E293B] bg-white/10 text-xs font-medium text-[#94A3B8]">
              +495
            </div>
          </div>
        </div>
      </div>

      {/* Right — Form panel */}
      <div className="flex flex-1 flex-col justify-center px-6 py-12 lg:px-16 xl:px-24">
        <div className="mx-auto w-full max-w-md">
          {/* Mobile logo */}
          <Link
            href="/"
            className="text-2xl font-bold text-[#6366F1] lg:hidden"
          >
            TrendyReports
          </Link>

          <h1 className="mt-10 text-3xl font-bold tracking-tight text-foreground lg:mt-0">
            Create your account
          </h1>
          <p className="mt-2 text-muted-foreground">
            Start your 14-day free trial. No credit card needed.
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
                or register with email
              </span>
            </div>
          </div>

          {/* Form */}
          <form className="mt-8 space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first-name">First name</Label>
                <Input
                  id="first-name"
                  type="text"
                  placeholder="Sarah"
                  className="h-12 rounded-lg"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last-name">Last name</Label>
                <Input
                  id="last-name"
                  type="text"
                  placeholder="Johnson"
                  className="h-12 rounded-lg"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reg-email">Email address</Label>
              <Input
                id="reg-email"
                type="email"
                placeholder="you@company.com"
                className="h-12 rounded-lg"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="reg-password">Password</Label>
              <div className="relative">
                <Input
                  id="reg-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a strong password"
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
              <p className="text-xs text-muted-foreground">
                Must be at least 8 characters with a number and symbol.
              </p>
            </div>

            <div className="flex items-start gap-2">
              <Checkbox id="terms" className="mt-0.5" />
              <Label
                htmlFor="terms"
                className="text-sm font-normal leading-relaxed text-muted-foreground"
              >
                {"I agree to the "}
                <Link href="#" className="text-[#6366F1] hover:text-[#4F46E5]">
                  Terms of Service
                </Link>
                {" and "}
                <Link href="#" className="text-[#6366F1] hover:text-[#4F46E5]">
                  Privacy Policy
                </Link>
              </Label>
            </div>

            <button
              type="submit"
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#6366F1] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5]"
            >
              Create account
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-semibold text-[#6366F1] hover:text-[#4F46E5]"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
