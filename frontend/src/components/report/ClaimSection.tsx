import type { Claim } from "../../types/research";
import { ClaimCard } from "../verification/ClaimCard";
import { EvidenceList } from "../evidence/EvidenceList";
import { ConfidenceCard } from "../confidence/ConfidenceCard";

interface ClaimSectionProps {
  claims: Claim[];
}

export function ClaimSection({ claims }: ClaimSectionProps) {
  if (!claims || claims.length === 0) {
    return (
      <div className="p-8 text-center border border-slate-200 border-dashed rounded-xl bg-slate-50">
        <p className="text-slate-500 font-medium">No verified claims available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      {claims.map((claim) => (
        <div key={claim.sub_claim_id} className="space-y-6">
          <ClaimCard claim={claim} />
          
          <div className="pl-4 md:pl-8 space-y-6 border-l-2 border-slate-100">
            {claim.confidence && (
              <ConfidenceCard 
                overallScore={claim.confidence.overall_score} 
                explanation={claim.confidence.explanation}
                breakdown={claim.confidence.breakdown}
              />
            )}
            
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                Supporting Evidence
              </h3>
              <EvidenceList evidence={claim.evidence} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
