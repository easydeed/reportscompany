/**
 * D-332 (LR-023): the schedule step says what Jerry decided on November 9.
 * Scheduled runs use schedule capacity, never the manual report allowance.
 * The old line ("Every run uses one report from your allowance") stated the
 * rule the ticker used to enforce, and both are gone.
 */
import { readFileSync } from "fs"
import { join } from "path"

const SOURCE = readFileSync(join(__dirname, "../components/unified-wizard/step-deliver.tsx"), "utf8")

describe("the schedule step's allowance line", () => {
  it("says scheduled runs don't use the monthly allowance", () => {
    expect(SOURCE).toContain(
      "\"Scheduled runs don't use your monthly report allowance. Each one pulls fresh data when it runs.\"",
    )
  })

  it("no longer says each run uses one report from the allowance", () => {
    expect(SOURCE).not.toMatch(/uses one report from your allowance/)
  })
})
