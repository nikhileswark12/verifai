import type { Evidence } from "../../types/research";
import { SourceBadge } from "./SourceBadge";

interface EvidenceCardProps {
  evidence: Evidence;
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h4 className="text-base font-semibold text-slate-900 leading-snug">
            {evidence.source.name}
          </h4>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-sm text-slate-500 font-medium">Domain:</span>
            <a
              href={evidence.source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline truncate max-w-[200px] sm:max-w-xs"
            >
              {evidence.source.domain}
            </a>
          </div>
        </div>
        <div className="flex-shrink-0">
          <SourceBadge tier={evidence.source.tier} />
        </div>
      </div>
      <div className="bg-slate-50 border-l-4 border-slate-300 p-4 rounded-r-lg">
        <p className="text-sm text-slate-700 italic">
          "{evidence.snippet}"
        </p>
      </div>
    </div>
  );
}
