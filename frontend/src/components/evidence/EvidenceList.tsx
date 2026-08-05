import type { Evidence } from "../../types/research";
import { EvidenceCard } from "./EvidenceCard";

interface EvidenceListProps {
  evidence: Evidence[];
}

export function EvidenceList({ evidence }: EvidenceListProps) {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="p-6 border border-slate-200 border-dashed rounded-xl bg-slate-50 text-center">
        <p className="text-slate-500 font-medium">No supporting evidence available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {evidence.map((item) => (
        <EvidenceCard key={item.id} evidence={item} />
      ))}
    </div>
  );
}
