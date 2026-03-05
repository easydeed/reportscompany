import type { SampleStat } from "./sample-data"

interface PreviewStackedStatsProps {
  stats: SampleStat[]
  primaryColor: string
}

export function PreviewStackedStats({ stats, primaryColor }: PreviewStackedStatsProps) {
  if (stats.length <= 4) {
    return (
      <div
        className="flex overflow-hidden rounded-md border"
        style={{ borderColor: `${primaryColor}15` }}
      >
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className="flex-1 px-2 py-2 text-center"
            style={{
              backgroundColor: `${primaryColor}05`,
              borderRight: i < stats.length - 1 ? `1px solid ${primaryColor}15` : undefined,
            }}
          >
            <div className="text-[8px] font-semibold uppercase tracking-wider text-stone-400">
              {stat.label}
            </div>
            <div className="text-[14px] font-bold text-stone-900 mt-0.5">{stat.value}</div>
            {stat.sub && (
              <div className="text-[8px] text-stone-500 mt-0.5">{stat.sub}</div>
            )}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="flex items-center justify-between rounded px-3 py-1.5"
          style={{ backgroundColor: `${primaryColor}06` }}
        >
          <span className="text-[10px] text-stone-500">{stat.label}</span>
          <div className="flex items-center gap-2">
            <span className="text-[12px] font-semibold text-stone-900">{stat.value}</span>
            {stat.sub && (
              <span className="text-[9px] text-stone-400">{stat.sub}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
