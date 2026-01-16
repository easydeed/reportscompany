"use client"

import { useState } from "react"
import { Accordion } from "@/components/ui/accordion"
import { ScheduleNameSection } from "./sections/schedule-name-section"
import { ReportTypeSection } from "./sections/report-type-section"
import { AreaSection } from "./sections/area-section"
import { AudienceFilterSection } from "./sections/audience-filter-section"
import { CadenceSection } from "./sections/cadence-section"
import { RecipientsSection } from "./sections/recipients-section"
import type { ScheduleBuilderState } from "@/lib/schedule-types"

interface ConfigurationPanelProps {
  state: ScheduleBuilderState
  updateState: <K extends keyof ScheduleBuilderState>(key: K, value: ScheduleBuilderState[K]) => void
}

export function ConfigurationPanel({ state, updateState }: ConfigurationPanelProps) {
  const [openSections, setOpenSections] = useState<string[]>(["name"])

  return (
    <div className="space-y-4">
      <Accordion type="multiple" value={openSections} onValueChange={setOpenSections} className="space-y-4">
        <ScheduleNameSection value={state.name} onChange={(value) => updateState("name", value)} />

        <ReportTypeSection
          reportType={state.reportType}
          lookbackDays={state.lookbackDays}
          onReportTypeChange={(value) => updateState("reportType", value)}
          onLookbackChange={(value) => updateState("lookbackDays", value)}
        />

        <AreaSection
          areaType={state.areaType}
          city={state.city}
          zipCodes={state.zipCodes}
          onAreaTypeChange={(value) => updateState("areaType", value)}
          onCityChange={(value) => updateState("city", value)}
          onZipCodesChange={(value) => updateState("zipCodes", value)}
        />

        {state.reportType === "new_listings_gallery" && (
          <AudienceFilterSection
            value={state.audienceFilter}
            onChange={(filter, name) => {
              updateState("audienceFilter", filter)
              updateState("audienceFilterName", name)
            }}
          />
        )}

        <CadenceSection
          cadence={state.cadence}
          weeklyDow={state.weeklyDow}
          monthlyDom={state.monthlyDom}
          sendHour={state.sendHour}
          sendMinute={state.sendMinute}
          timezone={state.timezone}
          onCadenceChange={(value) => updateState("cadence", value)}
          onWeeklyDowChange={(value) => updateState("weeklyDow", value)}
          onMonthlyDomChange={(value) => updateState("monthlyDom", value)}
          onSendHourChange={(value) => updateState("sendHour", value)}
          onSendMinuteChange={(value) => updateState("sendMinute", value)}
          onTimezoneChange={(value) => updateState("timezone", value)}
        />

        <RecipientsSection
          recipients={state.recipients}
          includeAttachment={state.includeAttachment}
          onRecipientsChange={(value) => updateState("recipients", value)}
          onIncludeAttachmentChange={(value) => updateState("includeAttachment", value)}
        />
      </Accordion>
    </div>
  )
}
