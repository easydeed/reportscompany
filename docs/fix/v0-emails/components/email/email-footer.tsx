import { Phone, Mail } from "lucide-react";
import Image from "next/image";

export function AgentFooter() {
  return (
    <div className="border-t border-border bg-[#1e3a5f]/[0.03] px-8 py-8">
      <div className="flex items-center gap-5">
        {/* Agent Photo */}
        <div className="h-20 w-20 shrink-0 overflow-hidden rounded-full border-2 border-[#1e3a5f]/20 bg-muted">
          <Image
            src="/images/agent-photo.jpg"
            alt="Sarah Chen, Senior Realtor"
            width={80}
            height={80}
            className="h-full w-full object-cover"
          />
        </div>
        {/* Agent Info */}
        <div className="flex-1">
          <p className="font-serif text-lg font-bold text-foreground">
            Sarah Chen
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Senior Realtor, DRE#01234567
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <a
              href="tel:3105550142"
              className="inline-flex items-center gap-1.5 rounded-md border border-[#1e3a5f]/15 bg-card px-3 py-1.5 text-xs font-medium text-[#1e3a5f] transition-colors hover:bg-[#1e3a5f]/[0.05]"
            >
              <Phone className="h-3 w-3" />
              (310) 555-0142
            </a>
            <a
              href="mailto:sarah@acmerealty.com"
              className="inline-flex items-center gap-1.5 rounded-md border border-[#1e3a5f]/15 bg-card px-3 py-1.5 text-xs font-medium text-[#1e3a5f] transition-colors hover:bg-[#1e3a5f]/[0.05]"
            >
              <Mail className="h-3 w-3" />
              sarah@acmerealty.com
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export function EmailDisclaimer() {
  return (
    <div className="rounded-b-lg border-t border-border bg-card px-8 py-5 text-center">
      <p className="text-[11px] text-muted-foreground">
        Powered by{" "}
        <span className="font-semibold text-foreground/70">TrendyReports</span>
      </p>
      <a
        href="#"
        className="mt-1 inline-block text-[11px] text-muted-foreground underline underline-offset-2 hover:text-foreground/70"
      >
        Unsubscribe
      </a>
    </div>
  );
}
