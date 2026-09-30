export interface InternetStatus {
  online: boolean;
  latency_ms: number | null;
  packet_loss_percent: number | null;
  message: string | null;
}

export interface StatusResult {
  internet: InternetStatus;
  local_ip: string | null;
  public_ip: string | null;
  gateway: string | null;
  dns_server: string | null;
}

export interface PingResult {
  host: string;
  status: "reachable" | "unreachable";
  latency_ms: number | null;
  packet_loss_percent: number;
  packets_sent: number;
  packets_received: number;
  message: string | null;
}

export interface DnsResult {
  hostname: string;
  status: "resolved" | "failed";
  addresses: string[];
  dns_server: string | null;
  response_time_ms: number | null;
  message: string | null;
}

export interface TracerouteHop {
  hop: number;
  address: string | null;
  latency_ms: number | null;
}

export interface TracerouteResult {
  target: string;
  status: "completed" | "incomplete" | "failed";
  hops: TracerouteHop[];
  message: string | null;
}

export interface PortCheckResult {
  host: string;
  port: number;
  status: "open" | "closed" | "timeout" | "error";
  response_time_ms: number | null;
  message: string | null;
}

export interface HistoryEntry {
  id: number;
  tool: string;
  target: string;
  summary: string;
  ok: boolean;
}

export type HistoryInput = Omit<HistoryEntry, "id">;
