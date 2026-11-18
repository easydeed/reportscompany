export type Recipient =
  | { type: "sponsored_agent"; id: string; name: string }
  | { type: "contact"; id: string; name: string; email: string }
  | { type: "group"; id: string; name: string; memberCount: number }
  | { type: "manual_email"; email: string }
