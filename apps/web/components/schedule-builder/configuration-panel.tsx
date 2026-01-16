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
  // Show audience filter only for new_listings or new_listings_gallery report types
  const showAudienceFilter = state.reportType === "new_listings" || state.reportType === "new_listings_gallery"

  // Auto-advance to next section
  const advanceToSection = (nextSection: string, delay = 300) => {
    setTimeout(() => {
      setExpandedSection(nextSection)
    }, delay)
  }

  // Section configurations with step numbers
  const getStepNumber = (section: string) => {
    const sections = ["name", "report-type", "area"]
    if (showAudienceFilter) sections.push("audience")
    sections.push("cadence", "recipients")
    return sections.indexOf(section) + 1
  }

  return (
    <div className="space-y-4">
      <ScheduleNameSection
        stepNumber={getStepNumber("name")}
        value={state.name}
        onChange={(name) => {
          updateState({ name })
          // Auto-advance when name is filled
          if (name.trim().length > 0 && expandedSection === "name") {
            advanceToSection("report-type")
          }
        }}
        isExpanded={expandedSection === "name"}
        onToggle={() => setExpandedSection(expandedSection === "name" ? "" : "name")}
      />

      <ReportTypeSection
        stepNumber={getStepNumber("report-type")}
        reportType={state.reportType}
        lookbackDays={state.lookbackDays}
        onChange={(updates) => {
          updateState(updates)
          // Auto-advance after selection
          if (expandedSection === "report-type") {
            advanceToSection("area")
          }
        }}
        isExpanded={expandedSection === "report-type"}
        onToggle={() => setExpandedSection(expandedSection === "report-type" ? "" : "report-type")}
      />

      <AreaSection
        stepNumber={getStepNumber("area")}
        areaType={state.areaType}
        city={state.city}
        zipCodes={state.zipCodes}
        onChange={(updates) => {
          updateState(updates)
          // Auto-advance when area is valid
          const willBeValid = updates.city || (updates.zipCodes && updates.zipCodes.length > 0)
          if (willBeValid && expandedSection === "area") {
            const nextSection = showAudienceFilter ? "audience" : "cadence"
            advanceToSection(nextSection)
          }
        }}
        isExpanded={expandedSection === "area"}
        onToggle={() => setExpandedSection(expandedSection === "area" ? "" : "area")}
      />

      {showAudienceFilter && (
        <AudienceFilterSection
          stepNumber={getStepNumber("audience")}
          value={state.audienceFilter}
          onChange={(audienceFilter, audienceFilterName) => {
            updateState({ audienceFilter, audienceFilterName })
            // Auto-advance after selection
            if (audienceFilter && expandedSection === "audience") {
              advanceToSection("cadence")
            }
          }}
          isExpanded={expandedSection === "audience"}
          onToggle={() => setExpandedSection(expandedSection === "audience" ? "" : "audience")}
        />
      )}

      <CadenceSection
        stepNumber={getStepNumber("cadence")}
        cadence={state.cadence}
        weeklyDow={state.weeklyDow}
        monthlyDom={state.monthlyDom}
        sendHour={state.sendHour}
        sendMinute={state.sendMinute}
        timezone={state.timezone}
        onChange={(updates) => {
          updateState(updates)
          // Auto-advance after cadence is set
          if (expandedSection === "cadence") {
            advanceToSection("recipients")
          }
        }}
        isExpanded={expandedSection === "cadence"}
        onToggle={() => setExpandedSection(expandedSection === "cadence" ? "" : "cadence")}
      />

      <RecipientsSection
        stepNumber={getStepNumber("recipients")}
        recipients={state.recipients}
        includeAttachment={state.includeAttachment}
        onChange={(updates) => updateState(updates)}
        isExpanded={expandedSection === "recipients"}
        onToggle={() => setExpandedSection(expandedSection === "recipients" ? "" : "recipients")}
      />
    </div>
  )
}
