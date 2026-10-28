/**
 * The social stories, rendered from what the report builders actually emit.
 *
 * `fixtures/social-results.json` is the output of each
 * `report_builders.build_*_result` over one synthetic market (60 listings,
 * mixed status), so a cell that reads a metric no builder produces shows up
 * here as the dash it would show on every real story.
 *
 * THE RULE: a dash means "missing this time", never "this report does not
 * calculate it". With every metric present, no story prints one.
 */
import * as fs from "fs";
import * as path from "path";
import { SOCIAL_TEMPLATE_MAP } from "@/lib/social-templates";
import results from "./fixtures/social-results.json";

const TEMPLATES = path.join(__dirname, "..", "templates", "social");
const BRANDS = ["#18235c", "#F59E0B", "#84CC16", "#DC2626", "#0D9488", "#7C3AED"];
const STAT_KINDS = ["market_snapshot", "new_listings", "closed", "inventory", "price_bands"];
const PHOTO_KINDS = ["new_listings_gallery", "featured_listings"];

function render(kind: string, primary: string): string {
  const { filename, builder } = SOCIAL_TEMPLATE_MAP[kind];
  const template = fs.readFileSync(path.join(TEMPLATES, filename), "utf8");
  return builder(template, {
    result_json: (results as Record<string, unknown>)[kind],
    brand: { primary_color: primary, display_name: "Jennifer Realty", contact_line1: "Jennifer Martinez" },
  });
}

function visibleText(html: string): string {
  return html.replace(/<style[\s\S]*?<\/style>/g, "").replace(/<[^>]+>/g, " ");
}

describe.each([...STAT_KINDS, ...PHOTO_KINDS])("%s story", (kind) => {
  it("prints no dash when the report has every metric", () => {
    const text = visibleText(render(kind, "#18235c"));
    expect(text).not.toContain("—");
  });

  it("never sets the brand as text, and never reads the retired accent", () => {
    const html = render(kind, "#F59E0B");
    expect(html).not.toContain("color:var(--pct-blue)");
    expect(html).not.toContain("--pct-accent");
    expect(html).toMatch(/--pct-ink: #[0-9a-f]{6};/);
    expect(html).toMatch(/--pct-on: #[0-9a-f]{6};/);
  });
});

it("the cells are the ones each report computes", () => {
  const labels = (kind: string) =>
    [...render(kind, "#18235c").matchAll(/text-transform:uppercase;color:#64748B">([^<]+)<\/div><\/div>/g)].map((m) => m[1]);
  expect(labels("market_snapshot")).toEqual(["Homes sold", "Days to sell", "Sale to list", "Months supply"]);
  expect(labels("new_listings")).toEqual(["Median asking", "Per sq ft", "Days on market"]);
  expect(labels("closed")).toEqual(["Median sale", "Days to sell", "Sale to list"]);
  expect(labels("inventory")).toEqual(["New this month", "Days on market", "Months supply"]);
});

// Renders for the browser contrast check (scripts outside the suite).
if (process.env.SOCIAL_DUMP_DIR) {
  it("dumps renders", () => {
    for (const kind of [...STAT_KINDS, ...PHOTO_KINDS]) {
      for (const b of BRANDS) {
        fs.writeFileSync(path.join(process.env.SOCIAL_DUMP_DIR as string, `${kind}--${b.slice(1)}.html`), render(kind, b));
      }
    }
  });
}
