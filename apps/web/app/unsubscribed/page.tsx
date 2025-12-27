"use client";

import { CheckCircle } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function UnsubscribedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Successfully Unsubscribed
          </h1>
          
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            You have been unsubscribed from our email notifications. 
            You will no longer receive scheduled reports from this sender.
          </p>
          
          <div className="space-y-3">
            <Link href="/">
              <Button variant="default" className="w-full">
                Return to Homepage
              </Button>
            </Link>
            
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Changed your mind?{" "}
              <Link href="/login" className="text-primary hover:underline">
                Log in
              </Link>{" "}
              to manage your email preferences.
            </p>
          </div>
        </div>
        
        <p className="text-center text-sm text-slate-500 mt-6">
          © {new Date().getFullYear()} TrendyReports. All rights reserved.
        </p>
      </div>
    </div>
  );
}

