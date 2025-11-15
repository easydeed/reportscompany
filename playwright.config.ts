import { defineConfig } from "@playwright/test";

export default defineConfig({
  use: {
    baseURL: process.env.E2E_BASE_URL || "https://reportscompany-web.vercel.app",
    trace: "on-first-retry",
    headless: true,
  },
  reporter: [["list"], ["html", { outputFolder: "playwright-report" }]],
});

