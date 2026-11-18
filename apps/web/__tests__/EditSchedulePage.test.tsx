import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import EditSchedulePage from "@/app/app/schedules/[id]/edit/page"
import ScheduleDetailPage from "@/app/app/schedules/[id]/page"

jest.mock("next/headers", () => ({ cookies: async () => ({ get: () => ({ value: "test-token" }) }) }))
const mockPush = jest.fn()
const mockRefresh = jest.fn()
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, refresh: mockRefresh }),
}))

const id = "fc631ec7-bbba-46ce-bdbc-ce864c4ac92a"
const endpoint = `/api/proxy/v1/schedules/${id}`
const people = [
  { type: "manual_email", email: "first@example.com" },
  { type: "manual_email", email: "second@example.com" },
  { type: "group", id: "group-1" },
  { type: "contact", id: "contact-1" },
  { type: "sponsored_agent", id: "agent-1" },
]
const schedule = {
  id, name: "Monthly round-up", active: false, report_type: "new_listings_gallery",
  city: null, zip_codes: ["02108", "02109"], filters: { preset_display_name: "Beach homes", minprice: 950000 },
  cadence: "monthly", monthly_dom: 26, weekly_dow: null, send_hour: 0, send_minute: 45,
  timezone: "America/New_York", include_attachment: false, lookback_days: 60,
  recipients: [people[0].email, ...people.slice(1).map(p => JSON.stringify(p))],
  resolved_recipients: people,
}
const mockFetch = global.fetch as jest.Mock
const response = (data: unknown, status = 200) => ({ ok: status === 200, status, json: async () => data })

async function openEdit(data: unknown, loseFirstReply = false) {
  mockFetch.mockImplementation(async (url: string, options?: RequestInit) => {
    if (options?.method === "GET" && url.endsWith(`/v1/schedules/${id}`)) {
      expect(options.headers).toEqual(expect.objectContaining({ Cookie: "mr_token=test-token" }))
      return response(data, data ? 200 : 404)
    }
    if (url === endpoint && options?.method === "PATCH") {
      if (loseFirstReply) {
        loseFirstReply = false
        throw new Error("Connection lost")
      }
      return response({ id, message: "Schedule updated" })
    }
    return response({}) // Preview, contacts and groups
  })
  const page = await EditSchedulePage({ params: Promise.resolve({ id }) })
  await act(async () => {
    render(<QueryClientProvider client={new QueryClient()}>{page}</QueryClientProvider>)
  })
}

function writes() {
  return mockFetch.mock.calls.filter(([, options]) => options?.method && options.method !== "GET")
    .map(([url, options]) => [url, options.method, JSON.parse(options.body)])
}
const save = () => within(screen.getByRole("banner")).getByRole("button", { name: "Update Schedule" })

it("opens the selected schedule’s edit route from the authenticated detail view", async () => {
  mockFetch.mockResolvedValue(response(schedule))
  render(await ScheduleDetailPage({ params: Promise.resolve({ id }) }))
  expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining(`/v1/schedules/${id}`), expect.objectContaining({
    method: "GET", headers: { Cookie: "mr_token=test-token" },
  }))
  fireEvent.click(screen.getByRole("button", { name: "Edit" }))
  expect(mockPush).toHaveBeenCalledWith(`/app/schedules/${id}/edit`)
})

it.each([true, false])("renames an existing schedule (active=%s) and safely retries a lost reply", async active => {
  await openEdit({ ...schedule, active }, true)
  expect(screen.getByLabelText("Schedule Name")).toHaveValue(schedule.name)
  expect(screen.getByLabelText("Active schedule")).toHaveProperty("checked", active)
  expect(screen.getByText("02108")).toBeInTheDocument()
  expect(screen.getAllByText("Beach homes").length).toBeGreaterThan(0)
  expect(screen.getByText("first@example.com")).toBeInTheDocument()
  expect(save()).toBeDisabled()
  fireEvent.change(screen.getByLabelText("Schedule Name"), { target: { value: " " } })
  expect(save()).toBeDisabled()
  fireEvent.change(screen.getByLabelText("Schedule Name"), { target: { value: "Updated name" } })
  fireEvent.click(save())
  await screen.findByText("Connection lost")
  expect(mockPush).not.toHaveBeenCalled()
  fireEvent.click(save())
  await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/app/schedules"))
  const rename = [endpoint, "PATCH", { name: "Updated name" }]
  expect(writes()).toEqual([rename, rename])
})

it.each([true, false])("changes only the status when toggling active=%s", async active => {
  await openEdit({ ...schedule, active })
  fireEvent.click(screen.getByLabelText("Active schedule"))
  fireEvent.click(save())
  await waitFor(() => expect(mockPush).toHaveBeenCalled())
  expect(writes()).toEqual([[endpoint, "PATCH", { active: !active }]])
})

it("allows editing an empty paused schedule but requires a recipient before activation", async () => {
  await openEdit({ ...schedule, recipients: [], resolved_recipients: [] })
  fireEvent.change(screen.getByLabelText("Schedule Name"), { target: { value: "Draft" } })
  expect(save()).toBeEnabled()
  fireEvent.click(screen.getByLabelText("Active schedule"))
  expect(save()).toBeDisabled()
  expect(writes()).toEqual([])
})

it("clears the saved city when switching to ZIP coverage", async () => {
  await openEdit({ ...schedule, city: "Downey", zip_codes: null })
  fireEvent.click(screen.getByRole("button", { name: "ZIP Codes" }))
  const input = screen.getByPlaceholderText("Add ZIP code (press Enter)")
  fireEvent.change(input, { target: { value: "02108" } })
  fireEvent.keyDown(input, { key: "Enter" })
  fireEvent.click(save())
  await waitFor(() => expect(mockPush).toHaveBeenCalled())
  expect(writes()).toEqual([[endpoint, "PATCH", { city: "", zip_codes: ["02108"] }]])
})

it("keeps all other recipients when removing one legacy email and clearing custom filters", async () => {
  await openEdit(schedule)
  fireEvent.click(screen.getByLabelText("Remove first@example.com"))
  fireEvent.click(screen.getByText("All Listings", { selector: "button" }))
  fireEvent.click(save())
  await waitFor(() => expect(mockPush).toHaveBeenCalled())
  expect(writes()).toEqual([[endpoint, "PATCH", { recipients: people.slice(1), filters: {} }]])
})

it.each([null, { ...schedule, active: "false" }, { ...schedule, id: "other" }])(
  "withholds the editor when the selected schedule cannot be verified", async data => {
    await openEdit(data)
    expect(screen.getByRole("link", { name: "Back to schedules" })).toBeInTheDocument()
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument()
    expect(writes()).toEqual([])
  },
)
