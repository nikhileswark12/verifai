import type { MappedAgentStatus } from "../../utils/agentStatus";

interface AgentStatusIconProps {
  status: MappedAgentStatus;
}

export function AgentStatusIcon({ status }: AgentStatusIconProps) {
  switch (status) {
    case "completed":
      return (
        <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center border border-emerald-200">
          <span className="text-emerald-700 text-sm font-bold">✓</span>
        </div>
      );
    case "active":
      return (
        <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center border border-blue-200">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse"></div>
        </div>
      );
    case "failed":
      return (
        <div className="w-6 h-6 rounded-full bg-rose-100 flex items-center justify-center border border-rose-200">
          <span className="text-rose-700 text-sm font-bold">!</span>
        </div>
      );
    case "waiting":
    default:
      return (
        <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200">
          <div className="w-1.5 h-1.5 rounded-full bg-slate-300"></div>
        </div>
      );
  }
}
