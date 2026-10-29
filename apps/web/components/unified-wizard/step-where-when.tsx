"use client"

/**
 * Step 3 — where, and how far back. Design's `Wizards v3`: City / ZIP pills,
 * the search or the ZIP list, then the window as five tiles.
 *
 * The city search is still CityCombobox, with its own styling (it is shared
 * with other forms), and adding a ZIP still behaves exactly as before. The deck's row of "nearby" city chips is not carried
 * over: it is five hard-coded Orange County cities, not anything the account
 * knows about.
 */
import { useState } from "react"
import { CityCombobox } from "@/components/shared/city-combobox"
import { REPORT_TYPES, type WizardState } from "./types"
import { FieldLabel, Pill, StepHeader } from "./wizard-ui"

interface StepWhereWhenProps {
  state: WizardState
  onChange: (patch: Partial<WizardState>) => void
}

const LOOKBACK_OPTIONS = [7, 14, 30, 60, 90] as const

export function StepWhereWhen({ state, onChange }: StepWhereWhenProps) {
  const [zipInput, setZipInput] = useState("")

  const addZip = () => {
    const zip = zipInput.trim()
    if (zip.length === 5 && /^\d{5}$/.test(zip) && !state.zipCodes.includes(zip)) {
      onChange({ zipCodes: [...state.zipCodes, zip] })
      setZipInput("")
    }
  }

  const removeZip = (zip: string) => {
    onChange({ zipCodes: state.zipCodes.filter((z) => z !== zip) })
  }

  const rt = REPORT_TYPES.find((r) => r.id === state.reportType)
  const lookbackNote = rt
    ? state.lookbackDays === rt.defaultLookback
      ? `${rt.defaultLookback} days is the default for ${rt.title}.`
      : `Default for ${rt.title} is ${rt.defaultLookback} days.`
    : null

  return (
    <div className="flex flex-col gap-[26px]">
      <StepHeader
        title="Where, and how far back?"
        sub="One city or up to five ZIPs. The window sets which sales count."
      />

      <div className="flex flex-col gap-2.5">
        <div className="flex gap-1.5">
          <Pill on={state.areaType === "city"} onClick={() => onChange({ areaType: "city" })}>
            City
          </Pill>
          <Pill on={state.areaType === "zip"} onClick={() => onChange({ areaType: "zip" })}>
            ZIP codes
          </Pill>
        </div>

        {state.areaType === "city" ? (
          <CityCombobox
            value={state.city}
            onChange={(city) => onChange({ city: city?.city || null })}
            placeholder="City, e.g. Irvine"
          />
        ) : (
          <div className="flex flex-col gap-2.5">
            <div className="flex gap-2">
              <input
                value={zipInput}
                onChange={(e) => setZipInput(e.target.value.replace(/\D/g, "").slice(0, 5))}
                onKeyDown={(e) => e.key === "Enter" && addZip()}
                placeholder="5-digit ZIP, press Enter"
                inputMode="numeric"
                maxLength={5}
                className="h-[52px] flex-1 rounded-[10px] border-[1.5px] border-[#D6D3CB] bg-white px-4 text-[17px] text-[#0F172A] outline-none focus:border-[#0F172A]"
              />
              <button
                type="button"
                onClick={addZip}
                disabled={zipInput.length !== 5}
                className="h-[52px] rounded-[10px] bg-[#0F172A] px-[18px] text-sm font-semibold text-white disabled:opacity-40"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              {state.zipCodes.map((zip) => (
                <button
                  key={zip}
                  type="button"
                  onClick={() => removeZip(zip)}
                  aria-label={`Remove ZIP ${zip}`}
                  className="rounded-full bg-[#0F172A] px-3 py-1.5 text-[13px] font-semibold text-white"
                >
                  {zip} ×
                </button>
              ))}
              <span className="text-[13px] text-[#94A3B8]">Up to 5</span>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2.5">
        <FieldLabel>Window</FieldLabel>
        <div className="grid grid-cols-5 gap-1.5">
          {LOOKBACK_OPTIONS.map((days) => {
            const on = state.lookbackDays === days
            return (
              <button
                key={days}
                type="button"
                aria-pressed={on}
                onClick={() => onChange({ lookbackDays: days })}
                className={
                  on
                    ? "rounded-[10px] border-[1.5px] border-[#0F172A] bg-[#0F172A] py-3 text-center text-white"
                    : "rounded-[10px] border-[1.5px] border-[#ECEAE3] bg-white py-3 text-center text-[#334155] hover:border-[#0F172A]"
                }
              >
                <span className="block text-lg font-bold leading-none">{days}</span>
                <span className="mt-[3px] block text-[11px]">days</span>
              </button>
            )
          })}
        </div>
        {lookbackNote && <span className="text-[13px] text-[#64748B]">{lookbackNote}</span>}
      </div>
    </div>
  )
}
