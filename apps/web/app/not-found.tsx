import Link from "next/link";
import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";

/**
 * Branded 404 (M2-T3).
 *
 * There was no not-found.tsx at all, so Next.js served its built-in default:
 * no nav, no footer, no link home, and the root layout's title. A visitor who
 * reached it — the footer linked to a route that 404s — had the browser back
 * button as their only exit.
 *
 * Note on the title: Next.js does not apply a `metadata` export from
 * not-found.tsx, so this page still inherits the root layout's default title.
 * Fixing that needs a route-level solution and is out of M2's scope; the
 * ticket's acceptance is nav plus a way out, both of which are here.
 */
export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteNav />

      <main className="flex flex-1 items-center justify-center px-6 py-24">
        <div className="mx-auto max-w-lg text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-[#6366F1]">
            404
          </p>
          <h1 className="mt-3 text-3xl font-semibold text-foreground md:text-4xl">
            We couldn&apos;t find that page
          </h1>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            The link may be out of date, or the page may have moved. Nothing is
            wrong with your account.
          </p>

          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-full bg-[#6366F1] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5]"
            >
              Back to homepage
            </Link>
            <Link
              href="/#pricing"
              className="inline-flex items-center justify-center rounded-full border border-border px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
            >
              See pricing
            </Link>
          </div>

          <p className="mt-8 text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-[#6366F1] hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
