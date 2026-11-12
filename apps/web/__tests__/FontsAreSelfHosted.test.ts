/**
 * The production build must not depend on fonts.googleapis.com. Every
 * `next/font/google` import made Vercel's build fetch from Google at build
 * time, and that fetch failing broke every production deploy (Node 26, then
 * Plus Jakarta Sans on Node 22). Fonts now load from the repository through
 * `next/font/local` (lib/fonts.ts).
 */
import { existsSync, readdirSync, readFileSync, statSync } from "fs"
import { join, resolve } from "path"

const WEB = resolve(__dirname, "..")
const SKIP = new Set(["node_modules", ".next", "__tests__", "public", "fonts"])

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    if (SKIP.has(name)) return []
    if (statSync(path).isDirectory()) return sources(path)
    return /\.(tsx?|jsx?|mjs)$/.test(name) ? [path] : []
  })
}

describe("web fonts are self-hosted", () => {
  it("nothing imports next/font/google", () => {
    const offenders = sources(WEB).filter((f) =>
      /from\s+["']next\/font\/google["']/.test(readFileSync(f, "utf8")),
    )
    expect(offenders).toEqual([])
  })

  it("every font file lib/fonts.ts names is in the repository", () => {
    const src = readFileSync(join(WEB, "lib/fonts.ts"), "utf8")
    const paths = [...src.matchAll(/path:\s*"([^"]+\.woff2)"/g)].map((m) => m[1])
    expect(paths.length).toBe(22)
    const missing = paths.filter((p) => !existsSync(join(WEB, "lib", p)))
    expect(missing).toEqual([])
  })

  it("the root layout still sets the Plus Jakarta Sans variable", () => {
    const fonts = readFileSync(join(WEB, "lib/fonts.ts"), "utf8")
    expect(fonts).toMatch(/variable:\s*"--font-jakarta"/)
    expect(readFileSync(join(WEB, "app/layout.tsx"), "utf8")).toMatch(/plusJakarta\.variable/)
  })
})
