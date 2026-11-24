import { render, screen, within } from "@testing-library/react"
import AdminEmails from "@/app/app/admin/emails/page"
import EmailLogs from "@/app/admin/(dashboard)/emails/page"

const params = new URLSearchParams()
jest.mock("next/navigation", () => ({
  useSearchParams: () => params,
  useRouter: () => ({ push: jest.fn() }),
}))

it.each([["admin email log", EmailLogs], ["app email log", AdminEmails]] as const)(
  "%s shows the recorded outcome for each message",
  async (_, Page) => {
    const emails = [
      ["sent", "Provider accepted"], ["suppressed", "Suppressed"],
      ["needs_review", "Needs review"], ["unknown", "Unknown"],
    ]
    const original = global.fetch
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({
      emails: emails.map(([outcome], i) => ({
        id: String(i), account_name: "Pilot", to_count: 1, subject: "Case " + outcome,
        provider: "sendgrid", status: "success", delivery_status: outcome,
        created_at: new Date().toISOString(),
      })),
    }) })
    try {
      render(<Page />)
      for (const [outcome, label] of emails) {
        const subject = await screen.findByText("Case " + outcome)
        expect(within(subject.closest("tr")!).getByText(label)).toBeInTheDocument()
      }
      expect(screen.queryByText("Delivered")).not.toBeInTheDocument()
    } finally {
      global.fetch = original
    }
  },
)

it.each([["admin email log", EmailLogs], ["app email log", AdminEmails]] as const)(
  "%s reports an unavailable log",
  async (_, Page) => {
    const original = global.fetch
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 503 })
    try {
      render(<Page />)
      expect(await screen.findByRole("alert")).toHaveTextContent("Couldn’t load the email log")
      expect(screen.queryByText("0")).not.toBeInTheDocument()
    } finally {
      global.fetch = original
    }
  },
)
