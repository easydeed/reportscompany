import dynamic from "next/dynamic";

const PropertyWizardContent = dynamic(
  () => import("./PropertyWizardContent"),
  {
    ssr: false,
    loading: () => (
      <div className="max-w-5xl mx-auto space-y-6 px-4 py-8">
        <div className="animate-pulse">
          {/* Header skeleton */}
          <div className="flex items-center gap-4 mb-6">
            <div className="w-10 h-10 bg-muted rounded-lg" />
            <div>
              <div className="h-7 bg-muted rounded w-56 mb-2" />
              <div className="h-4 bg-muted rounded w-72" />
            </div>
          </div>

          {/* Progress bar skeleton */}
          <div className="h-2 bg-muted rounded-full mb-4" />
          <div className="flex justify-between mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 bg-muted rounded-full" />
                <div className="h-3 bg-muted rounded w-16 hidden sm:block" />
              </div>
            ))}
          </div>

          {/* Card skeleton */}
          <div className="border rounded-lg p-6">
            <div className="h-6 bg-muted rounded w-48 mb-4" />
            <div className="space-y-3">
              <div className="h-10 bg-muted rounded" />
              <div className="h-10 bg-muted rounded" />
              <div className="h-24 bg-muted rounded" />
            </div>
          </div>
        </div>
      </div>
    ),
  }
);

export default function NewPropertyReportPage() {
  return <PropertyWizardContent />;
}
