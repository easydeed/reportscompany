"use client"

import { ScheduleNameSection } from "./sections/schedule-name-section"
import { ReportTypeSection } from "./sections/report-type-section"
import { AreaSection } from "./sections/area-section"
import { AudienceFilterSection } from "./sections/audience-filter-section"
import { CadenceSection } from "./sections/cadence-section"
import { RecipientsSection } from "./sections/recipients-section"
import type { ScheduleBuilderState } from "./types"

interface ConfigurationPanelProps {
  state: ScheduleBuilderState
  updateState: (updates: Partial<ScheduleBuilderState>) => void
  expandedSection: string
  setExpandedSection: (section: string) => void
}

export function ConfigurationPanel({
  state,
  updateState,
  expandedSection,
  setExpandedSection,
}: ConfigurationPanelProps) {
  const handleSectionToggle = (section: string) => {
    setExpandedSection(expandedSection === section ? "" : section)
  }

  // Show audience filter only for new_listings or new_listings_gallery report types
  const showAudienceFilter = state.reportType === "new_listings" || state.reportType === "new_listings_gallery"

  return (
    <div className="space-y-3">
      <ScheduleNameSection
        value={state.name}
        onChange={(name) => updateState({ name })}
        isExpanded={expandedSection === "name"}
        onToggle={() => handleSectionToggle("name")}
      />

      <ReportTypeSection
        reportType={state.reportType}
        lookbackDays={state.lookbackDays}
        onChange={(updates) => updateState(updates)}
        isExpanded={expandedSection === "report-type"}
        onToggle={() => handleSectionToggle("report-type")}
      />

      <AreaSection
        areaType={state.areaType}
        city={state.city}
        zipCodes={state.zipCodes}
        onChange={(updates) => updateState(updates)}
        isExpanded={expandedSection === "area"}
        onToggle={() => handleSectionToggle("area")}
      />

      {showAudienceFilter && (
        <AudienceFilterSection
          value={state.audienceFilter}
          onChange={(audienceFilter) => updateState({ audienceFilter })}
          isExpanded={expandedSection === "audience"}
          onToggle={() => handleSectionToggle("audience")}
        />
      )}

      <CadenceSection
        cadence={state.cadence}
        weeklyDow={state.weeklyDow}
        monthlyDom={state.monthlyDom}
        sendHour={state.sendHour}
        sendMinute={state.sendMinute}
        timezone={state.timezone}
        onChange={(updates) => updateState(updates)}
        isExpanded={expandedSection === "cadence"}
        onToggle={() => handleSectionToggle("cadence")}
      />

      <RecipientsSection
        recipients={state.recipients}
        includeAttachment={state.includeAttachment}
        onChange={(updates) => updateState(updates)}
        isExpanded={expandedSection === "recipients"}
        onToggle={() => handleSectionToggle("recipients")}
      />
    </div>
  )
}

