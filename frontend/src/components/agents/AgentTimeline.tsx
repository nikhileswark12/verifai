import type { ResearchStatusResponse } from "../../types/research";
import { AGENT_PIPELINE } from "../../constants/agents";
import { mapAgentStatus } from "../../utils/agentStatus";
import { AgentCard } from "./AgentCard";

interface AgentTimelineProps {
  status: ResearchStatusResponse | null;
}

export function AgentTimeline({ status }: AgentTimelineProps) {
  if (!status) return null;

  return (
    <div className="relative space-y-6 before:absolute before:inset-0 before:ml-7 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
      {AGENT_PIPELINE.map((agent) => {
        const rawStatus = status[agent.id];
        const mappedStatus = mapAgentStatus(rawStatus);

        return (
          <div key={agent.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
            <div className="hidden md:block w-1/2" />
            <div className="md:w-1/2 w-full pl-12 md:pl-0 md:group-odd:pr-12 md:group-even:pl-12">
              <AgentCard agent={agent} status={mappedStatus} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
