#!/usr/bin/env node
/**
 * Render authenticated routes, read computed styles off named elements, and
 * screenshot ONLY the routes that actually rendered.
 *
 * WHY THE SENTINEL EXISTS, AND WHY IT IS THE POINT OF THIS FILE
 * -------------------------------------------------------------
 * Every cheap version of this script produces green nonsense:
 *
 *   - `page.goto()` RESOLVES ON A 404. It reports the navigation, not the
 *     page. A redirect to /login is also a successful navigation.
 *   - `waitForSelector('body')` always succeeds. Every document has a body,
 *     including Next's error shell.
 *   - `getComputedStyle` on an error page returns real numbers. They are
 *     measurements of the error page.
 *
 * So assertions can pass in bulk against pages that never loaded, and the
 * screenshots look plausible. In a batch of twenty nobody checks whether page
 * nine rendered — which is why an unhealthy route here produces NO IMAGE
 * rather than a misleading one.
 *
 * A route is "the page" only when all four hold:
 *   1. the HTTP status is the one the manifest declares;
 *   2. the final URL is still the route — not /login, not /app, not /404;
 *   3. the manifest's `marker` selector is present AND non-empty;
 *   4. nothing on the page looks like an error shell.
 *
 * ROUTES THAT ARE SUPPOSED NOT TO RENDER
 * --------------------------------------
 * `/app/admin` with a non-admin token is a 404 BY DESIGN — `middleware.ts`
 * rewrites to /404 when ADMIN_CLOAK_404=1, else redirects to /app. Same for
 * /app/company without TITLE_COMPANY and /app/affiliate without
 * INDUSTRY_AFFILIATE. A harness that calls those failures is wrong, and one
 * that mints an all-powerful token for everything is not testing the product.
 * So every route declares `expect: "renders" | "blocked"` and its own token
 * claims, and `blocked` is asserted rather than tolerated.
 *
 * THE TOKEN IS UNSIGNED ON PURPOSE
 * --------------------------------
 * `middleware.ts` decodes without verifying (D-194), which is what makes a
 * local authenticated render possible at all. The API will refuse every call,
 * so panels show skeletons or errors — that is a real limit of this harness
 * and the reason the assertions are on CHROME, not on data.
 *
 * WHY COMPUTED STYLES AND NOT PIXELS
 * ----------------------------------
 * The per-route pixel noise floor moved 0.04% -> 4.56% on /app within an hour
 * (D-193). A diff of named properties off named elements does not drift when a
 * skeleton animation happens to be mid-cycle.
 *
 * USAGE
 *   node scripts/render_routes.mjs --out .render/before
 *   node scripts/render_routes.mjs --out .render/after
 *   node scripts/render_routes.mjs --compare .render/before .render/after
 *
 * Expects `next dev` already listening (default http://localhost:3100).
 */
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { createHmac } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const MANIFEST = join(ROOT, 'scripts/render-routes.json');

/**
 * The pre-installed browser. `playwright@1.57` in this repo does not match the
 * container's chromium-1194 build, so `launch()` with no path tries to
 * download and fails. Falling back to the bundled resolution when the pinned
 * path is absent keeps this working on a normal machine.
 */
const CHROMIUM = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const b64u = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');

/**
 * THE SIGNATURE IS THE DIFFERENCE BETWEEN CHROME AND CONTENT.
 *
 * `middleware.ts` decodes without verifying (D-194), so an UNSIGNED token is
 * enough to render the shell — which is all this harness could do before a
 * local API existed, and why 16 of 22 routes came back `degraded`.
 *
 * `apps/api` DOES verify (`authn.py` -> `jwt.decode(..., algorithms=["HS256"])`),
 * so a page's DATA needs a real signature over claims that name a real account.
 * Set RENDER_JWT_SECRET to the API's JWT_SECRET and the same manifest renders
 * pages instead of skeletons. Without it, this falls back to unsigned and the
 * harness still works — in chrome-only mode, which the output labels.
 */
const SECRET = process.env.RENDER_JWT_SECRET || null;

function mintToken(claims) {
  const payload = {
    account_id: '00000000-0000-0000-0000-000000000001',
    user_id: '00000000-0000-0000-0000-000000000002',
    account_type: 'REGULAR',
    exp: Math.floor(Date.now() / 1000) + 3600,
    ...claims,
  };
  const head = b64u({ alg: 'HS256', typ: 'JWT' });
  const body = b64u(payload);
  if (!SECRET) return `${head}.${body}.unsigned`;
  const sig = createHmac('sha256', SECRET).update(`${head}.${body}`).digest('base64url');
  return `${head}.${body}.${sig}`;
}

/** Probes read off the document itself — never off a coordinate. */
const PROBE = () => {
  const cs = getComputedStyle(document.documentElement);
  const tokens = {};
  for (const name of [
    '--primary', '--primary-foreground', '--link', '--foreground', '--body',
    '--muted', '--border', '--sidebar', '--surface-selected',
    '--border-selected', '--radius', '--radius-card',
  ]) tokens[name] = cs.getPropertyValue(name).trim();

  const of = (sel, props) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const s = getComputedStyle(el);
    const out = {};
    for (const p of props) out[p] = s[p];
    return out;
  };

  const BOX = ['backgroundColor', 'color', 'borderRadius', 'borderColor',
               'borderTopWidth', 'height', 'paddingTop', 'paddingLeft',
               'fontSize', 'fontWeight', 'letterSpacing', 'textTransform',
               'boxShadow'];

  // SELECTED BY `data-slot`, NOT BY CLASS.
  //
  // The first version read `[data-slot="card"], .rounded-2xl, .rounded-xl` —
  // selecting the card by the very class the restyle changes, so "the first
  // card" was a different element before and after and the diff was measuring
  // the selector. Every primitive here sets a `data-slot`, which is stable
  // across a restyle because it is an identity rather than a style.
  //
  // And the set has to COVER THE BATCH. Reading only body/h1/button/card
  // reported 6 of 25 routes changed for a batch that restyled seven
  // primitives, because tables, badges, inputs, switches and tabs were never
  // probed. An honest diff of an unmeasured thing is still zero.
  const slots = {};
  for (const [name, slot] of Object.entries({
    button: 'button', card: 'card', cardTitle: 'card-title',
    badge: 'badge', input: 'input', switch: 'switch',
    tableHead: 'table-head', tableCell: 'table-cell', tableRow: 'table-row',
    tabsList: 'tabs-list', tabsTrigger: 'tabs-trigger',
    select: 'select-trigger', dialog: 'dialog-content',
  })) {
    slots[name] = of(`[data-slot="${slot}"]`, BOX);
  }

  // ORDER, NOT STYLE.
  //
  // B3 moved Help below the usage block in the rail. That is a DOM-order
  // change with no computed-style consequence, so a style diff reports zero
  // and a reviewer concludes nothing happened. A structural batch needs a
  // structural probe: the sequence of the rail's landmarks, read top to
  // bottom, so "Help moved" is a visible change in the output.
  const rail = (() => {
    const root = document.querySelector('[data-slot="sidebar"], aside, nav');
    if (!root) return null;
    const seen = [];
    for (const el of root.querySelectorAll('a, button, [data-slot="sidebar-group-label"]')) {
      const t = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 24);
      if (t) seen.push(t);
    }
    return seen;
  })();

  return {
    tokens,
    rail,
    body: of('body', ['backgroundColor', 'color', 'fontSize', 'lineHeight', 'fontFamily']),
    h1: of('h1', ['fontSize', 'fontWeight', 'letterSpacing', 'lineHeight', 'color']),
    // THE TEXT, NOT JUST ITS STYLE. B4 replaced four stat tiles with a
    // sentence title and three composed panels — a content change with almost
    // no computed-style consequence, so the style probe reported one route
    // and one property (a link count) for a rewritten page. A batch that
    // changes what a page SAYS needs the page's words in the diff.
    h1text: (document.querySelector('h1')?.textContent || '').trim().slice(0, 80),
    landmarks: [...document.querySelectorAll('h1, h2, h3, p, [data-slot="card-title"]')]
      .map((el) => (el.textContent || '').trim().replace(/\s+/g, ' '))
      .filter((t) => t.length > 2 && t.length < 60)
      .slice(0, 24),
    slots,
    // Counted, not styled: a number that changes is a structural change.
    counts: {
      buttons: document.querySelectorAll('button').length,
      links: document.querySelectorAll('a').length,
      h1: document.querySelectorAll('h1').length,
      tables: document.querySelectorAll('table').length,
      // Per-primitive presence, so a diff can say "this route has no table"
      // rather than silently comparing two nulls.
      slotsPresent: Object.fromEntries(
        ['button', 'card', 'card-title', 'badge', 'input', 'switch',
         'table-head', 'table-cell', 'table-row', 'tabs-trigger'].map((s) =>
          [s, document.querySelectorAll(`[data-slot="${s}"]`).length])),
    },
  };
};

/**
 * Is this an error shell, and is the page's content actually here?
 *
 * `nextjs-portal` IS NOT AN ERROR. The first version of this treated its
 * presence as one, and every route in dev mode came back BROKEN with HTTP 200
 * and its own h1 found — because `next dev` mounts that element on every page
 * whether or not anything went wrong. A health check that fails everything is
 * safer than one that passes everything and still useless, so it is the
 * overlay's visible dialog that counts, not the host element.
 *
 * DEGRADED is the third state, and it is the one this harness runs in most.
 * There is no API behind a local render (the token is unsigned — D-194 is what
 * makes the render possible at all), so several authenticated pages sit in
 * their loading branch forever and others render an error card. Their SHELL is
 * real and worth measuring; their CONTENT is a spinner. Calling that `ok`
 * would put a skeleton's computed styles into a before/after table, and
 * calling it BROKEN would throw away the chrome that is genuinely there.
 */
const LOOKS_BROKEN = () => {
  const t = document.body?.innerText || '';
  const bad = [
    'This page could not be found',
    'Application error',
    'Unhandled Runtime Error',
    'Internal Server Error',
  ].filter((s) => t.includes(s));
  const dialog = document.querySelector('[data-nextjs-dialog], nextjs-portal [role="dialog"]');
  const errorish = [
    'Unable to Load', 'Error Loading', 'Something went wrong', 'Failed to load',
  ].filter((s) => t.includes(s));
  return {
    markers: bad,
    nextErrorOverlay: !!(dialog && dialog.getClientRects().length),
    // `animate-spin` is a spinner; `animate-pulse` is a skeleton. Counting
    // only the first reported /app/schedules as "no spinner, no heading",
    // which reads like a missing <h1> — it is a Skeleton branch that never
    // exits because `useSchedules` never resolves. Two different waits, both
    // of them "content has not arrived".
    spinners: document.querySelectorAll('.animate-spin').length,
    skeletons: document.querySelectorAll('.animate-pulse, [data-slot="skeleton"]').length,
    errorCards: errorish,
    bodyTextLength: t.trim().length,
  };
};

/**
 * `next dev` paints its own indicator — a dark circle, bottom left, over
 * whatever the rail has there. It is not product UI and never ships, but it
 * is IN EVERY SCREENSHOT, and the first before/after pair produced for review
 * showed it occluding "Property Reports 4/5" on one side and "Help Center" on
 * the other. A reviewer reads that as a layout defect the batch introduced.
 *
 * Hidden rather than configured off, so the harness works against any dev
 * server it is pointed at without needing next.config changed.
 */
const HIDE_DEV_CHROME = `
  nextjs-portal, [data-nextjs-toast], [data-nextjs-dev-tools-button],
  #__next-build-watcher { display: none !important; }
`;

async function visit(ctx, base, route) {
  const page = await ctx.newPage();
  const result = { route: route.path, token: route.token, expect: route.expect };
  try {
    await page.addStyleTag({ content: HIDE_DEV_CHROME }).catch(() => {});
    const res = await page.goto(base + route.path, {
      waitUntil: 'domcontentloaded', timeout: 45000,
    });
    // A server `redirect()` in a page component hands Playwright one document
    // and then Next soft-navigates to another, so an `evaluate` fired against
    // the first one dies with "Execution context was destroyed". Settling on
    // the network, with a URL that has stopped moving, is what makes the three
    // redirect stubs measurable instead of intermittently BROKEN.
    try {
      await page.waitForLoadState('networkidle', { timeout: 15000 });
    } catch { /* a page that never idles is still worth probing */ }
    await page.addStyleTag({ content: HIDE_DEV_CHROME }).catch(() => {});
    await page.waitForTimeout(route.settle ?? 1200);
    for (let i = 0; i < 3; i++) {
      const before = page.url();
      await page.waitForTimeout(250);
      if (page.url() === before) break;
    }

    result.status = res ? res.status() : null;
    result.finalPath = new URL(page.url()).pathname;
    result.broken = await page.evaluate(LOOKS_BROKEN);
    result.probe_counts = await page.evaluate(() => ({
      buttons: document.querySelectorAll('button').length,
      links: document.querySelectorAll('a').length,
    }));

    // ── THE SENTINEL ────────────────────────────────────────────────────
    const redirected = result.finalPath !== route.path;
    const marker = route.marker
      ? await page.evaluate((sel) => {
          const el = document.querySelector(sel);
          return el ? { found: true, text: (el.textContent || '').trim().slice(0, 60) } : { found: false };
        }, route.marker)
      : { found: null };
    result.marker = marker;

    // A declared redirect must land where the manifest says, and nowhere else.
    const wrongPlace = route.expectFinal
      ? result.finalPath !== route.expectFinal
      : redirected;

    const isShell = result.status === 200 &&
      !wrongPlace &&
      result.broken.markers.length === 0 &&
      !result.broken.nextErrorOverlay;

    // Content arrived, or it did not. Both can sit on a real shell.
    // A RATIO, NOT A THRESHOLD. One decorative skeleton — an avatar, a preview
    // tile — does not mean the page failed to arrive, and the first version of
    // this demoted four fully-rendered pages for having exactly one. But when
    // there are more placeholders than real controls, the content is not here.
    // Comparing against the page's own interactive count keeps that judgement
    // off a magic number.
    const controls = (result.probe_counts?.buttons ?? 0) + (result.probe_counts?.links ?? 0);
    const contentMissing =
      marker.found === false ||
      result.broken.spinners > 0 ||
      result.broken.errorCards.length > 0 ||
      result.broken.skeletons > controls;

    if (route.expect === 'blocked') {
      // Blocked is a PASS when the route refused: a redirect away, or the
      // cloaked 404. Rendering would be the failure.
      result.health = (redirected || result.status === 404) ? 'blocked-as-expected' : 'UNEXPECTEDLY-RENDERED';
    } else if (!isShell) {
      result.health = 'BROKEN';
    } else {
      result.health = contentMissing ? 'degraded' : 'ok';
    }

    // Styles and a screenshot only for a page proved to be the page. A
    // `degraded` page is measured and LABELLED, never silently compared with
    // an `ok` one — see `compare`.
    if (result.health === 'ok' || result.health === 'degraded') {
      result.probe = await page.evaluate(PROBE);
      result.screenshot = true;
    } else {
      result.probe = null;
      result.screenshot = false;   // a broken route gets NO image
    }
    return { result, page };
  } catch (err) {
    result.health = 'BROKEN';
    result.error = String(err).slice(0, 300);
    result.screenshot = false;
    return { result, page };
  }
}

function compare(beforeDir, afterDir) {
  const load = (d) => JSON.parse(readFileSync(join(d, 'routes.json'), 'utf8'));
  const a = load(beforeDir), b = load(afterDir);
  // Keyed by route AND token: the manifest renders /app twice, once as an
  // account with content and once as one with none, and they are different
  // measurements of the same path.
  const byRoute = (x) => Object.fromEntries(
    x.routes.map((r) => [`${r.route} [${r.token || '?'}/${r.expect || ''}]`, r]));
  const A = byRoute(a), B = byRoute(b);
  const routes = [...new Set([...Object.keys(A), ...Object.keys(B)])].sort();
  let changed = 0, unusable = 0;

  for (const route of routes) {
    const x = A[route], y = B[route];
    if (!x || !y) { console.log(`${route}\n  ONLY IN ONE RUN`); unusable++; continue; }
    // A route that refused in both runs has nothing to diff and is not a gap:
    // its health IS the assertion. Counting it as "not comparable" would make
    // a clean run exit non-zero and teach everyone to ignore the exit code.
    if (x.health === 'blocked-as-expected' && y.health === 'blocked-as-expected') continue;

    const usable = (h) => h === 'ok' || h === 'degraded';
    if (!usable(x.health) || !usable(y.health) || x.health !== y.health) {
      console.log(`${route}\n  NOT COMPARABLE — health ${x.health} -> ${y.health}`);
      unusable++;
      continue;
    }
    const diffs = [];
    const walk = (p, u, v) => {
      if (u && v && typeof u === 'object' && typeof v === 'object') {
        for (const k of new Set([...Object.keys(u), ...Object.keys(v)])) walk(`${p}.${k}`, u[k], v[k]);
      } else if (JSON.stringify(u) !== JSON.stringify(v)) {
        diffs.push(`${p}: ${JSON.stringify(u)} -> ${JSON.stringify(v)}`);
      }
    };
    walk('', x.probe, y.probe);
    if (diffs.length) {
      changed++;
      console.log(`${route}  (${diffs.length} changed)`);
      for (const d of diffs) console.log(`    ${d}`);
    }
  }
  console.log(`\n${'-'.repeat(60)}`);
  console.log(`${changed}/${routes.length} routes changed, ${unusable} not comparable`);
  if (!changed && !unusable) {
    console.log('Zero changes across every comparable route. On an unchanged ' +
                'tree that is the noise floor, and it is why this reads ' +
                'computed properties rather than pixels (D-193: the per-route ' +
                'pixel floor moved 0.04% -> 4.56% within an hour).');
  }
  if (unusable) {
    console.log('A route that is not comparable is NOT a route that did not change.');
    process.exitCode = 1;
  }
  return changed;
}

async function main() {
  const args = process.argv.slice(2);
  const ci = (f) => { const i = args.indexOf(f); return i === -1 ? null : args[i + 1]; };

  if (args[0] === '--compare') { compare(args[1], args[2]); return; }

  const out = ci('--out') || '.render/run';
  const base = ci('--base') || 'http://localhost:3100';
  const manifest = JSON.parse(readFileSync(MANIFEST, 'utf8'));
  mkdirSync(join(ROOT, out), { recursive: true });

  const launch = existsSync(CHROMIUM) ? { executablePath: CHROMIUM } : {};
  const browser = await chromium.launch(launch);
  const results = [];

  // `blocked` is a separate list in the manifest so the two intents read
  // differently, but both are exercised: a route that must refuse is only
  // proved to refuse by asking it.
  const all = [...manifest.routes, ...(manifest.blocked || [])];
  for (const route of all) {
    const ctx = await browser.newContext({ viewport: manifest.viewport });
    await ctx.addCookies([{
      name: 'mr_token',
      value: mintToken(manifest.tokens[route.token] || {}),
      domain: new URL(base).hostname, path: '/',
    }]);
    const { result, page } = await visit(ctx, base, route);
    if (result.screenshot) {
      const file = join(ROOT, out, (route.path + '_' + route.token).replace(/\W+/g, '_').replace(/^_/, '') + '.png');
      await page.screenshot({ path: file, fullPage: true });
      result.screenshotPath = file.slice(ROOT.length + 1);
    }
    results.push(result);
    const tag = result.health === 'ok' ? 'ok ' : result.health === 'degraded' ? 'deg'
              : result.health.startsWith('blocked') ? 'blk' : '!! ';
    console.log(`${tag} ${(route.path + ' [' + route.token + ']').padEnd(40)} ${String(result.status).padEnd(4)} ${result.health}`);
    await ctx.close();
  }
  await browser.close();

  writeFileSync(join(ROOT, out, 'routes.json'),
    JSON.stringify({ base, when: new Date().toISOString(),
                     signed: !!SECRET, routes: results }, null, 2));

  const broken = results.filter((r) => r.health === 'BROKEN' || r.health === 'UNEXPECTEDLY-RENDERED');
  const unexpected = results.filter((r) => r.health === 'UNEXPECTEDLY-RENDERED');
  console.log(`\n${'-'.repeat(60)}`);
  console.log(SECRET
    ? 'token SIGNED — the API can serve data, so `degraded` means a real gap'
    : 'token UNSIGNED — chrome-only mode: the API refuses every call, so '
      + 'most routes WILL be degraded and that is the harness, not the product');
  console.log(`${results.filter((r) => r.health === 'ok').length} rendered, ` +
              `${results.filter((r) => r.health === 'degraded').length} degraded (shell real, content absent), ` +
              `${results.filter((r) => r.health.startsWith('blocked')).length} blocked as expected, ` +
              `${broken.length} broken`);
  const degraded = results.filter((r) => r.health === 'degraded');
  if (degraded.length) {
    console.log('\nDEGRADED — chrome is measurable, page content is not:');
    for (const r of degraded) {
      console.log(`  ${r.route.padEnd(26)} spinners=${r.broken.spinners} ` +
                  `skeletons=${r.broken.skeletons} ` +
                  `errorCards=${JSON.stringify(r.broken.errorCards)} ` +
                  `marker=${r.marker.found === false ? 'MISSING' : JSON.stringify(r.marker.text)}`);
    }
  }
  if (broken.length) {
    console.log('\nBROKEN — no styles read, no screenshot taken:');
    for (const r of broken) {
      console.log(`  ${r.route}  status=${r.status} final=${r.finalPath} ` +
                  `marker=${JSON.stringify(r.marker)} ${r.error || ''}`);
    }
  }
  if (unexpected.length) {
    console.log('\nUNEXPECTEDLY RENDERED — a route the middleware should have refused:');
    for (const r of unexpected) console.log(`  ${r.route}`);
  }
  if (broken.length || unexpected.length) process.exitCode = 1;
}

main();
