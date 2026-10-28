/**
 * The confirm page is the only place a footer-link opt-out happens: nothing is
 * sent until the person taps "Unsubscribe", and the tap POSTs the address and
 * token from the link, unchanged.
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

let params = new URLSearchParams();
jest.mock("next/navigation", () => ({ useSearchParams: () => params }));
jest.mock("next/link", () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => children }));

import UnsubscribedPage from "@/app/unsubscribed/page";

describe("/unsubscribed?status=confirm", () => {
  beforeEach(() => {
    params = new URLSearchParams("status=confirm&email=a%2Bb%40x.com&token=t0k");
  });

  it("sends nothing on load", () => {
    const fetchSpy = jest.fn();
    global.fetch = fetchSpy as unknown as typeof fetch;
    render(<UnsubscribedPage />);
    expect(screen.getByText("Stop these emails?")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("one tap posts the link's address and token, then confirms", async () => {
    const fetchSpy = jest.fn().mockResolvedValue({ ok: true, status: 200 });
    global.fetch = fetchSpy as unknown as typeof fetch;
    render(<UnsubscribedPage />);
    fireEvent.click(screen.getByRole("button", { name: "Unsubscribe" }));
    await waitFor(() => expect(screen.getByText("You've been unsubscribed")).toBeInTheDocument());
    const [url, init] = fetchSpy.mock.calls[0];
    expect(url).toBe("/api/v1/email/unsubscribe");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ email: "a+b@x.com", token: "t0k", reason: "user_request" });
  });

  it("a token that does not verify says so, and does not claim success", async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 400 }) as unknown as typeof fetch;
    render(<UnsubscribedPage />);
    fireEvent.click(screen.getByRole("button", { name: "Unsubscribe" }));
    await waitFor(() => expect(screen.getByText("We couldn't verify this link")).toBeInTheDocument());
  });
});
