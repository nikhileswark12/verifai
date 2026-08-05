import { useState, useEffect } from "react";
import { researchApi } from "../api/research";
import { API_CONSTANTS } from "../constants/api";
import type {
  ResearchStatusResponse,
  ResearchResultResponse,
} from "../types/research";

export function useCreateResearch() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const createResearch = async (query: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await researchApi.createResearch(query);
      setJobId(response.job_id);
      return response.job_id;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create research";
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { createResearch, isLoading, error, jobId };
}

export function useResearchStatus(jobId: string | null) {
  const [status, setStatus] = useState<ResearchStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setStatus(null);
      return;
    }

    let isMounted = true;
    let timeoutId: number;

    const poll = async () => {
      try {
        setIsLoading(true);
        const data = await researchApi.getResearchStatus(jobId);
        
        if (!isMounted) return;
        
        setStatus(data);
        setError(null);

        // Continue polling if not completed/failed
        const isCompleted = data.status === "completed" || data.status === "failed";
        const allAgentsDone = data.report === "done" || data.report === "failed";
        
        if (!isCompleted && !allAgentsDone) {
          timeoutId = window.setTimeout(poll, API_CONSTANTS.POLL_INTERVAL);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        const errorMessage = err instanceof Error ? err.message : "Failed to fetch status";
        setError(errorMessage);
        // On network error, we might choose to retry or stop. 
        // We'll stop for simplicity on hard error.
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    poll();

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [jobId]);

  return { status, isLoading, error };
}

export function useResearchResult(jobId: string | null, enabled: boolean = false) {
  const [result, setResult] = useState<ResearchResultResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId || !enabled) {
      return;
    }

    let isMounted = true;

    const fetchResult = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await researchApi.getResearchResult(jobId);
        if (isMounted) {
          setResult(data);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const errorMessage = err instanceof Error ? err.message : "Failed to fetch result";
          setError(errorMessage);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchResult();

    return () => {
      isMounted = false;
    };
  }, [jobId, enabled]);

  return { result, isLoading, error };
}
