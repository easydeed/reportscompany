// Screenshots the property-report preview images for render_property_previews.py.
// Input: a jobs file {out, jobs: [{theme_id, html, pages}]}. One JPEG per
// `<section class="sheet sheet-{page}">`, at 510x660 (the 816x1056 letter
// page at 0.625), plus the cover again as {theme_id}.jpg. A page missing from
// the render is an error, never a silent gap in the wizard.
import { chromium } from 'playwright'
import { readFileSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'

const { out, jobs } = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {})
const page = await browser.newPage({ viewport: { width: 816, height: 1056 }, deviceScaleFactor: 0.625 })
for (const job of jobs) {
  await page.goto('file://' + job.html, { waitUntil: 'networkidle' })
  await page.evaluate(() => document.fonts.ready)
  mkdirSync(join(out, 'pages', String(job.theme_id)), { recursive: true })
  for (const name of job.pages) {
    const sheet = await page.$(`section.sheet.sheet-${name}`)
    if (!sheet) throw new Error(`theme ${job.theme_id}: no sheet-${name} in the render`)
    await sheet.screenshot({ path: join(out, 'pages', String(job.theme_id), `${name}.jpg`), type: 'jpeg', quality: 82 })
    if (name === 'cover') await sheet.screenshot({ path: join(out, `${job.theme_id}.jpg`), type: 'jpeg', quality: 82 })
  }
  console.log(`theme ${job.theme_id}: ${job.pages.length} pages`)
}
await browser.close()
