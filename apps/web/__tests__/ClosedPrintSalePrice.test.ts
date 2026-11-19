/**
 * The Closed Sales print report (/print/{id}, restored by #305) shows only a
 * recorded sale price in its "Close Price" column. It used to fall back to the
 * asking price (`close_price || list_price`), the same mistake #314 removed
 * from the Market Snapshot headline and LR-018 removed from the worker.
 */
import * as fs from "fs";
import * as path from "path";
import { buildClosedHtml } from "@/lib/templates";

const TEMPLATE = fs.readFileSync(path.join(__dirname, "..", "templates", "trendy-closed.html"), "utf8");

function closedRow(closePrice: number | null) {
  const data = {
    result_json: {
      city: "Irvine",
      lookback_days: 30,
      counts: { Closed: 1, Active: 0 },
      metrics: { median_close_price: closePrice, median_list_price: 755000 },
      listings_sample: [{
        status: "Closed",
        city: "Irvine",
        street_address: "1 Sandpiper Ln",
        list_price: 755000,
        close_price: closePrice,
        bedrooms: 3,
        bathrooms: 2,
        sqft: 1500,
        days_on_market: 12,
        close_date: "2026-11-01T00:00:00Z",
      }],
    },
    brand: { display_name: "Example Realty" },
  };
  const html = buildClosedHtml(TEMPLATE, data);
  const row = html.match(/<td>[^<]*<\/td>\s*<td>1 Sandpiper Ln<\/td>\s*<td class="t-right">([^<]*)<\/td>/);
  return { html, price: row?.[1] };
}

it.each([
  [null, "—"],
  [0, "—"],
  [640000, "$640,000"],
])("the Close Price column shows only a recorded sale price (close_price %p)", (closePrice, shown) => {
  const { html, price } = closedRow(closePrice as number | null);
  expect(price).toBe(shown);
  if (closePrice !== 640000) expect(html).not.toContain("$755,000");
});
