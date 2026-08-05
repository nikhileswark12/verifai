import type { ResearchStatusResponse } from "../../types/research";
import { Badge } from "../ui/Badge";
import { RESEARCH_UI_TEXT } from "../../constants/research";
import { AgentTimeline } from "../agents/AgentTimeline";

interface ResearchProgressProps {
  status: ResearchStatusResponse | null;
  isLoading: boolean;
}

export function ResearchProgress({ status, isLoading }: ResearchProgressProps) {
  if (isLoading && !status) {
    return (
      <div className="flex flex-col items-center justify-center p-8 space-y-4">
        <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <p className="text-slate-600 font-medium">Connecting to VerifAI Engine...</p>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">
            {RESEARCH_UI_TEXT.STATUS_HEADER}
          </h3>
          <p className="text-sm text-slate-500 font-mono mt-1">
            Job ID: {status.job_id}
          </p>
        </div>
        <Badge variant={status.status === "failed" ? "error" : status.status === "completed" ? "success" : "warning"}>
          {status.status?.toUpperCase() || "UNKNOWN"}
        </Badge>
      </div>

      <div className="py-4">
        <AgentTimeline status={status} />
      </div>
      
      {status.status === "completed" && (
        <div className="pt-4 text-center">
          <p className="text-emerald-600 font-medium mb-4">Research pipeline completed successfully.</p>
        </div>
      )}
    </div>
  );
}
