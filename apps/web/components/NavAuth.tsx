"use client"

export default function NavAuth() {
  async function logout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" })
    } catch {}
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

