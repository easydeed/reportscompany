import { act, fireEvent, render, screen } from "@testing-library/react";
import { CmaExperience } from "@/app/cma/[code]/cma-client";

jest.mock("@/hooks/useGooglePlaces", () => ({ ensureGooglePlaces: jest.fn(async () => {}) }));

beforeAll(() => {
  // The preview measures its container in a browser. This unit test renders text only.
  global.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
});
afterEach(() => { jest.useRealTimers(); });

it.each([
  ["lookup_limit", "Too many searches from this device. Try again in 2 minutes."],
  ["lookup_busy", "Search is busy right now. Try again in a few minutes."],
])("shows the homeowner the %s response", async (code, detail) => {
  jest.useFakeTimers();
  jest.mocked(fetch).mockResolvedValueOnce({
    ok: false, status: 429, json: async () => ({ code, detail }),
  } as Response);
  render(<CmaExperience code="sample" isDemo={false} initialAddress="1 Generated Street"
    source={{ name: "Generated Agent", company_name: null, license_number: null,
      phone: null, photo_url: null, theme_color: "#123456" }} />);
  fireEvent.click(screen.getByRole("button", { name: /find my home/i }));
  await act(async () => { await jest.advanceTimersByTimeAsync(3100); });
  expect(screen.getByText(detail)).toBeVisible();
});
