import { apiClient } from "./client";
import type {
  ResearchRequest,
  ResearchAcceptedResponse,
  ResearchStatusResponse,
  ResearchResultResponse,
  ResearchReport,
  HealthResponse,
} from "../types/research";

export const researchApi = {
  createResearch: async (query: string): Promise<ResearchAcceptedResponse> => {
    const data: ResearchRequest = { query };
    return apiClient.post<ResearchAcceptedResponse>("/research", data);
  },

  getResearchStatus: async (jobId: string): Promise<ResearchStatusResponse> => {
    return apiClient.get<ResearchStatusResponse>(`/research/${jobId}`);
  },

  getResearchResult: async (jobId: string): Promise<ResearchResultResponse> => {
    const data = await apiClient.get<ResearchReport | ResearchResultResponse>(`/research/${jobId}/result`);
    if ("executive_summary" in data) {
      return { status: "completed", report: data };
    }
    return data;
  },

  healthCheck: async (): Promise<HealthResponse> => {
    return apiClient.get<HealthResponse>("/health");
  },
};
