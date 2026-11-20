import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import AdminReportsPage from "@/app/app/admin/reports/page"

const mockToast = jest.fn()
const mockSearch = new URLSearchParams()
jest.mock("@/components/ui/use-toast", () => ({ useToast: () => ({ toast: mockToast }) }))
jest.mock("next/navigation", () => ({ useRouter: () => ({}), useSearchParams: () => mockSearch }))

const report = {
  id: "r1", report_type: "market_snapshot", account_name: "Test", created_at: "2026-11-13",
}

test("an interrupted manual retry stays actionable and shows the returned worker status", async () => {
  const message = "Generation-only recovery attempt 2 of 3. Status: completed."
  const fetchMock = global.fetch as jest.Mock
  fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({
    reports: [{ ...report, status: "processing", has_retry: true }],
  }) })
  fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ status: "completed", message }) })
  render(<AdminReportsPage />)
  fireEvent.click(await screen.findByRole("button", { name: "Retry" }))
  expect(await screen.findByText("completed")).toBeInTheDocument()
  expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ description: message }))
  expect(screen.queryByRole("button", { name: "Retry" })).toBeNull()
})

test("a delivery refusal reaches the operator and leaves the report failed", async () => {
  const message = "Review the original delivery. No report or email was queued."
  const fetchMock = global.fetch as jest.Mock
  fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({ reports: [{ ...report, status: "failed" }] }) })
  fetchMock.mockResolvedValueOnce({ ok: false, json: async () => ({ detail: message }) })
  const log = jest.spyOn(console, "error").mockImplementation(() => {})
  try {
    render(<AdminReportsPage />)
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }))
    await waitFor(() => expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ description: message })))
    expect(screen.getByText("failed")).toBeInTheDocument()
  } finally {
    log.mockRestore()
  }
})
