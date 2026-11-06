import { useState, useEffect } from "react";
import { researchApi } from "../api/research";
import { API_CONSTANTS } from "../constants/api";
import type {
  ResearchStatusResponse,
  ResearchResultResponse,
} from "../types/research";

const retryDelay = (attempt: number) =>
  Math.min(API_CONSTANTS.POLL_INTERVAL * 2 ** (attempt - 1), 15000);

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
      setError(null);
      return;
    }

    let isMounted = true;
    let timeoutId: number | undefined;
    let retries = 0;

    const poll = async () => {
      if (!isMounted) return;
      let retryScheduled = false;

      try {
        setIsLoading(true);
        const data = await researchApi.getResearchStatus(jobId);
        if (!isMounted) return;

        retries = 0;
        setStatus(data);
        setError(null);

        const isTerminal = data.status === "completed" || data.status === "failed";
        const reportStatus = data.agent_status?.report ?? data.report;
        const reportTerminal = reportStatus === "done" || reportStatus === "error" || reportStatus === "failed";
        if (!isTerminal && !reportTerminal) {
          timeoutId = window.setTimeout(poll, API_CONSTANTS.POLL_INTERVAL);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        retries += 1;
        if (retries <= API_CONSTANTS.MAX_RETRIES) {
          retryScheduled = true;
          timeoutId = window.setTimeout(poll, retryDelay(retries));
        } else {
          const errorMessage = err instanceof Error ? err.message : "Failed to fetch status";
          setError(errorMessage);
        }
      } finally {
        if (isMounted && !retryScheduled) setIsLoading(false);
      }
    };

    poll();

    return () => {
      isMounted = false;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
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
    let timeoutId: number | undefined;
    let retries = 0;

    const fetchResult = async () => {
      if (!isMounted) return;
      let retryScheduled = false;
      setIsLoading(true);

      try {
        const data = await researchApi.getResearchResult(jobId);
        if (!isMounted) return;

        retries = 0;
        setResult(data);
        setError(null);
        if (!data.report && data.status !== "failed") {
          timeoutId = window.setTimeout(fetchResult, API_CONSTANTS.POLL_INTERVAL);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        retries += 1;
        if (retries <= API_CONSTANTS.MAX_RETRIES) {
          retryScheduled = true;
          timeoutId = window.setTimeout(fetchResult, retryDelay(retries));
        } else {
          const errorMessage = err instanceof Error ? err.message : "Failed to fetch result";
          setError(errorMessage);
        }
      } finally {
        if (isMounted && !retryScheduled) setIsLoading(false);
      }
    };

    fetchResult();

    return () => {
      isMounted = false;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [jobId, enabled]);

  return { result, isLoading, error };
}
