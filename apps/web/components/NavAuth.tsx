"use client"

export default function NavAuth() {
  async function logout() {
    try {
      // Use correct logout route that clears the mr_token cookie
      await fetch("/api/proxy/v1/auth/logout", { 
        method: "POST",
        credentials: "include"
      })
    } catch (err) {
      console.error("Logout error:", err)
    }
    window.location.href = "/login"
  }

  return (
    <button
      onClick={logout}
      className="rounded border px-3 py-1.5 text-sm hover:bg-slate-50"
      title="Sign out"
    >
      Logout
    </button>
  )
}

