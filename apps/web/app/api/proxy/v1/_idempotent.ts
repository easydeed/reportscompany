import { NextResponse } from "next/server";

/**
 * LR-024 (design rev 3): the API behind this proxy has no /v1/idempotent/*
 * route, so it predates the key contract and ran nothing. Say so: nothing was
 * created, and the same key may be sent again once a supporting API answers.
 */
export function idempotentCreateUnavailable() {
  return NextResponse.json(
    {
      error: "idempotent_create_unavailable",
      message: "We can't create this right now. Nothing was created.",
    },
    { status: 503, headers: { "Cache-Control": "no-store" } },
  );
}
