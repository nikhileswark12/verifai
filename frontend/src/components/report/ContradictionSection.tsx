import type { ContradictionPair } from "../../types/research";
import { Badge } from "../ui/Badge";
import { Card, CardContent } from "../ui/Card";

interface ContradictionSectionProps {
  contradictions?: ContradictionPair[];
}

export function ContradictionSection({ contradictions }: ContradictionSectionProps) {
  if (!contradictions || contradictions.length === 0) {
    return (
      <div className="p-8 text-center border border-slate-200 border-dashed rounded-xl bg-slate-50">
        <p className="text-slate-500 font-medium">No contradictions detected.</p>
      </div>
    );
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "DIRECT": return "Direct disagreement";
      case "TEMPORAL": return "Different time periods";
      case "CONTEXTUAL": return "Contextual conflict";
      case "PARTIAL": return "Partial disagreement";
      case "NONE":
      default: return "Unknown";
    }
  };

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case "HIGH": return "error";
      case "MEDIUM": return "warning";
      case "LOW": return "neutral";
      default: return "neutral";
    }
  };

  return (
    <div className="space-y-6">
      {contradictions.map((pair, idx) => (
        <Card key={idx} className="border-rose-200 shadow-sm">
          <CardContent className="p-6 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-3">
                <Badge variant="neutral">{getTypeLabel(pair.type)}</Badge>
                <Badge variant={getSeverityVariant(pair.severity)}>{pair.severity} SEVERITY</Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 items-center">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-slate-500 uppercase">Claim A</h4>
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 h-full">
                  <p className="text-slate-900 font-medium">"{pair.claim_a}"</p>
                  <p className="text-sm text-blue-600 mt-2 truncate">Source: {pair.source_a}</p>
                </div>
              </div>

              <div className="hidden md:flex flex-col items-center justify-center text-slate-400 font-bold px-2">
                VS
              </div>
              <div className="md:hidden flex items-center justify-center text-slate-400 font-bold py-2">
                VS
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-slate-500 uppercase">Claim B</h4>
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 h-full">
                  <p className="text-slate-900 font-medium">"{pair.claim_b}"</p>
                  <p className="text-sm text-blue-600 mt-2 truncate">Source: {pair.source_b}</p>
                </div>
              </div>
            </div>

            <div className="bg-rose-50/50 p-4 rounded-lg border border-rose-100">
              <h4 className="text-sm font-semibold text-rose-800 mb-1">Analysis</h4>
              <p className="text-sm text-rose-700 leading-relaxed">
                {pair.explanation}
              </p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
