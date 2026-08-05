import type { ConfidenceBreakdown as BreakdownType } from "../../types/research";
import { ConfidenceBreakdown } from "./ConfidenceBreakdown";
import { ConfidenceBar } from "./ConfidenceBar";
import { Card, CardContent } from "../ui/Card";

interface ConfidenceCardProps {
  overallScore: number;
  explanation: string;
  breakdown?: BreakdownType;
}

export function ConfidenceCard({ overallScore, explanation, breakdown }: ConfidenceCardProps) {
  return (
    <Card>
      <CardContent className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Overall Confidence</h3>
          <ConfidenceBar score={overallScore} />
        </div>
        
        <div className="bg-slate-50 border border-slate-100 rounded-lg p-4">
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
            {explanation}
          </p>
        </div>

        {breakdown && (
          <div className="pt-4 border-t border-slate-100">
            <ConfidenceBreakdown breakdown={breakdown} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
