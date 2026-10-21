// Learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";

// Mock Next.js router
jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      pathname: "/",
      query: {},
      asPath: "/",
    };
  },
  usePathname() {
    return "/";
  },
  useSearchParams() {
    return new URLSearchParams();
  },
}));

// Mock fetch globally
global.fetch = jest.fn();

// Reset mocks after each test.
//
// `clearAllMocks` empties the CALL LOG and leaves `mockResolvedValueOnce`
// QUEUES in place, so a value a test queued and did not consume is handed to
// the next test's first fetch. Three failures in AccountSwitcher.test.tsx
// were that, and the signature is the one that wastes an afternoon: each
// test passes alone and fails in the file. The global fetch mock is reset
// outright so no queue can cross a test boundary.
afterEach(() => {
  jest.clearAllMocks();
  if (jest.isMockFunction(global.fetch)) {
    (global.fetch as jest.Mock).mockReset();
  }
});

