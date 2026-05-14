/**
 * DEBT-001 — regression matrix for isBuilderRoute(pathname).
 *
 * The /app shell decides whether a route renders in "builder mode" (no
 * sidebar) or "normal mode" (with sidebar). Earlier, builder mode also
 * skipped the QueryProvider; misclassifying a list view as builder mode
 * crashed every page that used useQuery() (HOTFIX-SCHEDULES-LAYOUT).
 *
 * QueryProvider is now hoisted to app/app/layout.tsx, so this matrix only
 * controls the sidebar/full-bleed layout. It still matters: a list page
 * misclassified as builder mode loses its navigation chrome, and a builder
 * page misclassified as normal mode gets a confusing sidebar.
 *
 * Note on tooling: the ticket requested Vitest, but apps/web uses Jest
 * (see jest.config.ts and the existing PlanPage.test.tsx). The assertions
 * and matrix are identical to what was requested for Vitest.
 */

import { isBuilderRoute } from "../app/app-layout"

describe("isBuilderRoute", () => {
  it("returns false for list views", () => {
    expect(isBuilderRoute("/app/schedules")).toBe(false)
    expect(isBuilderRoute("/app/schedules/")).toBe(false)
    expect(isBuilderRoute("/app/reports")).toBe(false)
  })

  it("returns true for new routes", () => {
    expect(isBuilderRoute("/app/schedules/new")).toBe(true)
    // /app/reports/new is the market-report wizard — it renders full-bleed
    // without the sidebar, same as the other "new" wizards.
    // (BUILDER-ROUTES-REPORTS)
    expect(isBuilderRoute("/app/reports/new")).toBe(true)
    expect(isBuilderRoute("/app/property/new")).toBe(true)
  })

  it("returns true for edit routes with id", () => {
    expect(isBuilderRoute("/app/schedules/abc-123/edit")).toBe(true)
    expect(isBuilderRoute("/app/schedules/abc-123/edit/")).toBe(true)
  })

  it("returns false for detail views", () => {
    expect(isBuilderRoute("/app/schedules/abc-123")).toBe(false)
    expect(isBuilderRoute("/app/reports/abc-123")).toBe(false)
  })

  it("returns false for malformed edit-like paths", () => {
    // No id segment between /schedules/ and /edit — must not match.
    expect(isBuilderRoute("/app/schedules//edit")).toBe(false)
    // /edit prefix on another resource isn't a schedule-edit route.
    expect(isBuilderRoute("/app/reports/abc-123/edit")).toBe(false)
  })

  it("returns false for null pathname", () => {
    expect(isBuilderRoute(null)).toBe(false)
  })
})
