import type { Claim } from "../../types/research";
import { Card, CardContent } from "../ui/Card";
import { VerificationStatus } from "./VerificationStatus";

interface ClaimCardProps {
  claim: Claim;
}

export function ClaimCard({ claim }: ClaimCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-3 flex-grow">
            <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Claim</h4>
            <p className="text-lg font-medium text-slate-900 leading-relaxed">
              "{claim.text}"
            </p>
          </div>
          <div className="flex flex-col items-start md:items-end gap-2 flex-shrink-0">
            <VerificationStatus status={claim.status} />
            <div className="text-sm text-slate-600 font-medium">
              Confidence: <span className="font-bold text-slate-900">{claim.confidence.overall_score}%</span>
            </div>
            <div className="text-sm text-slate-500">
              Evidence: {claim.evidence.length} sources
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
