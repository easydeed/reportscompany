/**
 * @jest-environment node
 *
 * The footer unsubscribe link's GET changes nothing.
 *
 * Security scanners (Microsoft Safe Links, Mimecast, Proofpoint) open every
 * link in a message before a person does. While this GET did the unsubscribe,
 * a scanner opening the footer removed a contact who never asked. It now only
 * redirects to the confirm page; the POST is the opt-out.
 */
import { NextRequest } from "next/server";
import { GET, POST } from "@/app/api/v1/email/unsubscribe/route";

const LINK = "https://trendyreports.io/api/v1/email/unsubscribe?token=t0k&email=a%2Bb%40x.com";

describe("GET /api/v1/email/unsubscribe", () => {
  const fetchSpy = jest.fn();
  beforeEach(() => {
    fetchSpy.mockReset();
    global.fetch = fetchSpy as unknown as typeof fetch;
  });

  it("calls nothing: a scanner opening the link unsubscribes no one", async () => {
    await GET(new NextRequest(LINK));
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("redirects to the confirm page with the same address and token", async () => {
    const res = await GET(new NextRequest(LINK));
    const to = new URL(res.headers.get("location") || "");
    expect(to.pathname).toBe("/unsubscribed");
    expect(to.searchParams.get("status")).toBe("confirm");
    expect(to.searchParams.get("email")).toBe("a+b@x.com");
    expect(to.searchParams.get("token")).toBe("t0k");
  });

  it("a link missing its token lands on invalid, not confirm", async () => {
    const res = await GET(new NextRequest("https://trendyreports.io/api/v1/email/unsubscribe?email=a%40x.com"));
    expect(new URL(res.headers.get("location") || "").searchParams.get("status")).toBe("invalid");
  });
});

describe("POST /api/v1/email/unsubscribe (the confirm button)", () => {
  it("forwards the address and token to the API's opt-out", async () => {
    const fetchSpy = jest.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    global.fetch = fetchSpy as unknown as typeof fetch;
    const body = { email: "a+b@x.com", token: "t0k", reason: "user_request" };
    const res = await POST(new NextRequest("https://trendyreports.io/api/v1/email/unsubscribe", {
      method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json" } }));
    expect(res.status).toBe(200);
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toMatch(/\/v1\/email\/unsubscribe$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual(body);
  });
});
