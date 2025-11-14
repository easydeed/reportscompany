"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const nextPath = searchParams.get("next") || "/app";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
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
        const data = await res.json();
        throw new Error(data.detail || "Login failed");
      }

      // Backend sets mr_token cookie via Set-Cookie header
      // No need to manually set cookie here
      
      // Redirect to next path or dashboard
      router.push(nextPath);
    } catch (err: any) {
      setError(err.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "#0f172a" }}>
      <div style={{ width: "100%", maxWidth: "400px", padding: "32px", backgroundColor: "#1e293b", borderRadius: "8px", boxShadow: "0 4px 6px rgba(0,0,0,0.3)" }}>
        <h1 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "8px", color: "#f1f5f9" }}>
          Sign in
        </h1>
        <p style={{ color: "#94a3b8", marginBottom: "24px" }}>
          Enter your credentials to access your account
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "16px" }}>
            <label htmlFor="email" style={{ display: "block", marginBottom: "8px", color: "#e2e8f0", fontSize: "14px" }}>
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "8px 12px",
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: "#f1f5f9",
                fontSize: "14px",
              }}
            />
          </div>

          <div style={{ marginBottom: "24px" }}>
            <label htmlFor="password" style={{ display: "block", marginBottom: "8px", color: "#e2e8f0", fontSize: "14px" }}>
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "8px 12px",
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: "#f1f5f9",
                fontSize: "14px",
              }}
            />
          </div>

          {error && (
            <div style={{ marginBottom: "16px", padding: "12px", backgroundColor: "#7f1d1d", border: "1px solid #991b1b", borderRadius: "4px", color: "#fecaca", fontSize: "14px" }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "10px",
              backgroundColor: loading ? "#475569" : "#8b5cf6",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              fontSize: "14px",
              fontWeight: "500",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "#0f172a", color: "#fff" }}>Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}

