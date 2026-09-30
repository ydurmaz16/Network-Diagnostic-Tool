import type {
  DnsResult,
  PingResult,
  PortCheckResult,
  StatusResult,
  TracerouteResult,
} from "./types";

/** An error whose message is safe to show to the user. */
export class ApiError extends Error {}

const REQUEST_TIMEOUT_MS = 100_000; // traceroute can take a while

async function request<T>(path: string, body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(path, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The test took too long and was cancelled.");
    }
    throw new ApiError("Cannot reach the diagnostic server. Make sure the backend is running.");
  } finally {
    clearTimeout(timer);
  }

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON response; handled below.
  }

  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
        ? data.detail
        : "The server returned an unexpected error.";
    throw new ApiError(detail);
  }
  if (data === null) {
    throw new ApiError("The server returned an unexpected response.");
  }
  return data as T;
}

export const getStatus = () => request<StatusResult>("/api/network/status");
export const runPing = (target: string) => request<PingResult>("/api/network/ping", { target });
export const runDns = (hostname: string) => request<DnsResult>("/api/network/dns", { hostname });
export const runTraceroute = (target: string) =>
  request<TracerouteResult>("/api/network/traceroute", { target });
export const checkPort = (host: string, port: number) =>
  request<PortCheckResult>("/api/network/port-check", { host, port });
