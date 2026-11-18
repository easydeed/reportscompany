import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import { isIP } from "node:net";
import type { NextRequest } from "next/server";

function sign(secret: string, value: string): string {
  return createHmac("sha256", secret).update(value).digest("hex");
}

export function publicLookupVisitor(req: NextRequest, path: string) {
  const headers = new Headers({ "Content-Type": "application/json" });
  const cookieSecret = process.env.VISITOR_COOKIE_SECRET;
  const proxySecret = process.env.PROXY_SHARED_SECRET;
  // Opt in only after the operator verifies ownership of the edge-set address.
  // Unconfigured deployments count all public traffic in the API's direct bucket.
  if (process.env.LOOKUP_TRUST_VERIFIED_PROXY !== "1" || !cookieSecret || !proxySecret) {
    return { headers };
  }
  const ip = req.headers.get("x-real-ip");
  if (!ip || !isIP(ip) || ip.includes("%")) return { headers };

  const cookie = req.cookies.get("tr_v")?.value ?? "";
  const parts = /^([a-f0-9]{32})\.([a-f0-9]{64})$/.exec(cookie);
  const valid = parts && timingSafeEqual(Buffer.from(parts[2], "hex"),
    Buffer.from(sign(cookieSecret, parts[1]), "hex"));
  const visitor = valid ? parts[1] : randomBytes(16).toString("hex");
  const ts = String(Math.floor(Date.now() / 1000));
  headers.set("X-TR-Visitor-IP", ip);
  headers.set("X-TR-Visitor-Id", visitor);
  headers.set("X-TR-Proxy-Ts", ts);
  headers.set("X-TR-Proxy-Sig", sign(proxySecret, `${ts}\n${req.method} ${path}\n${ip}\n${visitor}`));
  return { headers, newCookie: valid ? undefined : `${visitor}.${sign(cookieSecret, visitor)}` };
}
