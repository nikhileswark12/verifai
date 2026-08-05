import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Card, CardContent } from "../components/ui/Card";
import { ResearchForm } from "../components/research/ResearchForm";
import { ResearchProgress } from "../components/research/ResearchProgress";
import { ResearchError } from "../components/research/ResearchError";
import { useCreateResearch, useResearchStatus } from "../hooks/useResearch";
import type { ResearchWorkflowState } from "../types/research";
import { Button } from "../components/ui/Button";

export function Research() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const jobIdParam = searchParams.get("jobId");

  const { createResearch, isLoading: isSubmitting, error: submitError } = useCreateResearch();
  const { status, isLoading: isPolling, error: pollError } = useResearchStatus(jobIdParam);

  const [workflowState, setWorkflowState] = useState<ResearchWorkflowState>(jobIdParam ? "running" : "idle");

  useEffect(() => {
    if (submitError || pollError || status?.status === "failed") {
      setWorkflowState("error");
    } else if (status?.status === "completed") {
      setWorkflowState("completed");
    } else if (jobIdParam) {
      setWorkflowState("running");
    } else {
      setWorkflowState("idle");
    }
  }, [status, submitError, pollError, jobIdParam]);

  const handleSubmit = async (query: string) => {
    setWorkflowState("submitting");
    try {
      const id = await createResearch(query);
      if (id) {
        setSearchParams({ jobId: id });
      }
    } catch {
      // Error is handled by hook and effect
    }
  };

  const handleReset = () => {
    setSearchParams({});
    setWorkflowState("idle");
  };

  const activeError = submitError || pollError || (status?.status === "failed" ? "Research execution failed" : null);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Research Workspace</h2>
        {workflowState === "completed" && jobIdParam && (
          <Button onClick={() => navigate(`/report/${jobIdParam}`)} variant="primary">
            View Final Report
          </Button>
        )}
        {(workflowState === "running" || workflowState === "error" || workflowState === "completed") && (
          <Button onClick={handleReset} variant="ghost" size="sm">
            Start New Query
          </Button>
        )}
      </div>

      <Card>
        <CardContent>
          {workflowState === "idle" || workflowState === "submitting" ? (
            <ResearchForm onSubmit={handleSubmit} isLoading={isSubmitting} />
          ) : (
            <div className="space-y-8">
              {activeError ? (
                <ResearchError error={activeError} onRetry={handleReset} />
              ) : (
                <ResearchProgress status={status} isLoading={isPolling} />
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
