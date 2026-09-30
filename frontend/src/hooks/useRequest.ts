import { useCallback, useState } from "react";
import { ApiError } from "../api";

/** Tracks loading / error / data for one async request. */
export function useRequest<T>() {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async (fn: () => Promise<T>): Promise<T | null> => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await fn();
      setData(result);
      return result;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /** Show a client-side validation message without calling the API. */
  const fail = useCallback((message: string) => {
    setData(null);
    setError(message);
  }, []);

  return { data, error, loading, run, fail };
}
