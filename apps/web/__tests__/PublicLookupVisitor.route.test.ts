/** @jest-environment node */
import { createHmac } from "node:crypto";
import { NextRequest } from "next/server";
import { POST } from "@/app/api/proxy/v1/cma/[code]/search/route";

const page = { params: Promise.resolve({ code: "generated" }) };
const path = "/v1/cma/generated/search";
const ip = "192.0.2.11";

function request(cookie?: string) {
  return new NextRequest("https://web.invalid/api/proxy" + path, {
    method: "POST",
    headers: { "x-real-ip": ip, ...(cookie ? { cookie } : {}) },
    body: JSON.stringify({ address: "1 Generated Street" }),
  });
}

beforeEach(() => {
  jest.replaceProperty(process, "env", { ...process.env, NEXT_PUBLIC_API_BASE: "https://api.invalid",
    LOOKUP_TRUST_VERIFIED_PROXY: "0", VISITOR_COOKIE_SECRET: "unit-cookie", PROXY_SHARED_SECRET: "unit-proxy" });
  global.fetch = jest.fn().mockImplementation(async () => Response.json([]));
});
afterEach(() => { jest.restoreAllMocks(); });

it("starts in the shared direct mode without issuing a cookie", async () => {
  const response = await POST(request(), page);
  const [, init] = jest.mocked(fetch).mock.calls[0];
  expect([...new Headers(init?.headers).keys()]).toEqual(["content-type"]);
  expect(response.cookies.get("tr_v")).toBeUndefined();
  expect(await response.json()).toEqual([]);
});

it("signs and reuses a generated visitor cookie when locally configured", async () => {
  process.env.LOOKUP_TRUST_VERIFIED_PROXY = "1";
  const response = await POST(request(), page);
  const cookie = response.cookies.get("tr_v")!;
  expect(cookie).toMatchObject({ httpOnly: true, secure: true, sameSite: "lax", maxAge: 2592000, path: "/" });
  const [visitor, cookieSig] = cookie.value.split(".");
  expect(visitor).toMatch(/^[a-f0-9]{32}$/);
  expect(cookieSig).toBe(createHmac("sha256", "unit-cookie").update(visitor).digest("hex"));
  const second = await POST(request("tr_v=" + cookie.value), page);
  expect(second.cookies.get("tr_v")).toBeUndefined();
  for (const [to, init] of jest.mocked(fetch).mock.calls) {
    expect(String(to)).toBe("https://api.invalid" + path);
    const headers = new Headers(init?.headers);
    expect(headers.get("x-tr-visitor-id")).toBe(visitor);
    expect(headers.get("x-tr-visitor-ip")).toBe(ip);
    const message = [headers.get("x-tr-proxy-ts"), "POST " + path, ip, visitor].join("\n");
    expect(headers.get("x-tr-proxy-sig")).toBe(createHmac("sha256", "unit-proxy").update(message).digest("hex"));
  }
});

it("passes the retry time, remaining budget and homeowner message through", async () => {
  const body = { code: "lookup_limit", detail: "Too many searches from this device. Try again in 2 minutes." };
  jest.mocked(fetch).mockResolvedValueOnce(Response.json(body, {
    status: 429, headers: { "Retry-After": "90", "RateLimit-Limit": "20",
      "RateLimit-Remaining": "0", "RateLimit-Reset": "90" },
  }));
  const response = await POST(request(), page);
  expect(response.status).toBe(429);
  expect(await response.json()).toEqual(body);
  expect(["Retry-After", "RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset"]
    .map(name => response.headers.get(name))).toEqual(["90", "20", "0", "90"]);
});
