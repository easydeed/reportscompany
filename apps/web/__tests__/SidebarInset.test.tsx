/**
 * D-044 — SidebarInset must keep `min-w-0`.
 *
 * SidebarInset renders the <main> that holds the entire authenticated UI, as a
 * flex child of the app shell's row container. A flex item's default
 * `min-width: auto` refuses to shrink below its content's intrinsic width, and
 * `flex-1` does not override it. Without `min-w-0` the inset stayed pinned at
 * its content width at every viewport — measured at 1012px on the Title Rep
 * dashboard at both 1024px and 1142px — pushing the topbar's account menu off
 * the right edge and giving the document a horizontal scrollbar. It also
 * defeated every `overflow-x-auto` wrapper nested inside, because a wide
 * table's intrinsic width propagated straight through this element.
 *
 * Why this is a className assertion and not a layout assertion: jsdom does not
 * do layout. `getBoundingClientRect()` returns zeroes and `scrollWidth` is
 * always 0, so the actual defect — an element failing to shrink — is not
 * observable in this environment at all. The real proof is a browser
 * measurement across three account types and three viewport widths; this test
 * exists to stop the one class that produced it from being deleted, which is
 * something jsdom CAN check.
 *
 * The className is read off the rendered element rather than the source file so
 * that `cn()`/tailwind-merge actually runs: passing a conflicting width class
 * from a caller could silently drop `min-w-0`, and the case below renders with
 * the exact className app/app-layout.tsx passes in production.
 *
 * NOTE: this suite does not currently run in CI — see D-041 (`pnpm` is never
 * installed on the runner) and D-042 (`ts-node` missing, so jest.config.ts
 * cannot be parsed). Both must be fixed for this test to protect anything.
 */

import { render } from "@testing-library/react"
import { SidebarInset } from "@/components/ui/sidebar"

describe("SidebarInset", () => {
  it("carries min-w-0 so the shell can shrink below its content width", () => {
    const { container } = render(<SidebarInset />)
    const main = container.querySelector("main")

    expect(main).not.toBeNull()
    expect(main!.className.split(/\s+/)).toContain("min-w-0")
  })

  it("keeps min-w-0 when app-layout passes its own classes", () => {
    // The exact className app/app-layout.tsx uses. tailwind-merge resolves
    // conflicts by category, and a caller-supplied class must not be able to
    // strip the min-width reset.
    const { container } = render(<SidebarInset className="flex flex-col" />)
    const classes = container.querySelector("main")!.className.split(/\s+/)

    expect(classes).toContain("min-w-0")
    expect(classes).toContain("flex-col")
  })

  it("still shrinks when a caller supplies an explicit width", () => {
    const { container } = render(<SidebarInset className="w-1/2" />)
    const classes = container.querySelector("main")!.className.split(/\s+/)

    // w-* and min-w-* are different tailwind-merge groups, so overriding the
    // width must not take min-w-0 with it. If this ever fails, tailwind-merge's
    // grouping changed and the fix needs re-checking in a real browser.
    expect(classes).toContain("min-w-0")
  })
})
