export const emailOutcomeLabels: Record<string, string> = {
  sent: "Provider accepted",
  delivered: "Delivered",
  failed: "Failed",
  bounced: "Bounced",
  needs_review: "Needs review",
  blocked_unverified: "Blocked · sender unverified",
  duplicate_suppressed: "Duplicate prevented",
  suppressed: "Suppressed",
  sending: "Sending",
  queued: "Queued",
  pending: "Pending",
  unknown: "Unknown",
}

export function emailOutcomeLabel(status?: string): string {
  return emailOutcomeLabels[status ?? "unknown"] ?? "Unknown"
}

export function providerAccepted(status?: string): boolean {
  return status === "sent" || status === "delivered"
}
