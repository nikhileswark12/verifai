import type { ConfidenceBreakdown as BreakdownType } from "../../types/research";
import { ConfidenceBar } from "./ConfidenceBar";

interface ConfidenceBreakdownProps {
  breakdown: BreakdownType;
}

export function ConfidenceBreakdown({ breakdown }: ConfidenceBreakdownProps) {
  const metrics = [
    { label: "Source Reliability", value: breakdown.reliability_score },
    { label: "Evidence Agreement", value: breakdown.agreement_score },
    { label: "Source Count", value: breakdown.source_count_score },
    { label: "Citation Score", value: breakdown.citation_score }
  ];

  return (
    <div className="space-y-4">
      <h5 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-3">
        Confidence Breakdown
      </h5>
      <div className="space-y-3">
        {metrics.map((m) => (
          <div key={m.label} className="grid grid-cols-1 sm:grid-cols-[200px_1fr] items-center gap-2 sm:gap-4">
            <span className="text-sm text-slate-600 font-medium">{m.label}</span>
            <ConfidenceBar score={m.value} />
          </div>
        ))}
      </div>
    </div>
  );
}
