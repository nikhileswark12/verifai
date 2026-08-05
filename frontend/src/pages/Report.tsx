import { useParams, Link } from "react-router-dom";
import { useResearchResult } from "../hooks/useResearch";
import { Button } from "../components/ui/Button";
import { ExecutiveSummary } from "../components/report/ExecutiveSummary";
import { AssessmentCard } from "../components/report/AssessmentCard";
import { ClaimSection } from "../components/report/ClaimSection";
import { ContradictionSection } from "../components/report/ContradictionSection";
import { ReferenceList } from "../components/report/ReferenceList";

export function Report() {
  const { jobId } = useParams<{ jobId: string }>();
  const { result, isLoading, error } = useResearchResult(jobId || null, !!jobId);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <p className="text-slate-600 font-medium">Loading research results...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-4xl mx-auto p-6 mt-12 text-center">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-8">
          <p className="text-rose-600 font-medium mb-6">
            Unable to load research results.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/">
              <Button variant="secondary">Return Home</Button>
            </Link>
            {jobId && (
              <Link to={`/research?jobId=${jobId}`}>
                <Button variant="primary">View Job Status</Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    );
  }

  const report = result.report;

  if (!report) {
    return (
      <div className="max-w-4xl mx-auto p-6 mt-12 text-center border border-slate-200 border-dashed rounded-xl bg-slate-50">
        <p className="text-slate-600">No report data found for this job.</p>
        <Link to="/" className="mt-4 inline-block">
          <Button variant="secondary">Start New Research</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-24">
      <header className="space-y-6 pt-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-slate-900">Research Report</h1>
          <Link to="/">
            <Button variant="ghost">New Research</Button>
          </Link>
        </div>
        <div className="bg-slate-50 border-l-4 border-blue-500 p-6 rounded-r-xl">
          <p className="text-xl font-medium text-slate-800 leading-snug">
            {report.query}
          </p>
        </div>
      </header>

      <section>
        <ExecutiveSummary summary={report.executive_summary} />
      </section>

      <section>
        <AssessmentCard assessment={report.overall_assessment} />
      </section>

      <section className="space-y-6">
        <h2 className="text-xl font-bold text-slate-900 border-b border-slate-200 pb-2">
          Verified Claims
        </h2>
        <ClaimSection claims={report.claims} />
      </section>

      <section className="space-y-6">
        <h2 className="text-xl font-bold text-slate-900 border-b border-slate-200 pb-2">
          Contradictions Detected
        </h2>
        <ContradictionSection contradictions={report.contradictions} />
      </section>

      <section className="space-y-6">
        <h2 className="text-xl font-bold text-slate-900 border-b border-slate-200 pb-2">
          References
        </h2>
        <ReferenceList references={report.references} />
      </section>
    </div>
  );
}
