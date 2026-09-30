import type { ReactNode } from "react";
import { fmtMs, fmtPercent } from "../format";
import type { StatusResult } from "../types";

function Card({
  title,
  accent,
  children,
}: {
  title: string;
  accent: string;
  children: ReactNode;
}) {
  return (
    <div className={`rounded-lg border border-line border-l-4 bg-white p-4 ${accent}`}>
      <h3 className="text-sm font-medium text-slate-600">{title}</h3>
      <div className="mt-2 space-y-1">{children}</div>
    </div>
  );
}

function Line({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex justify-between gap-3 text-sm">
      <span className="text-slate-600">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

export default function StatusCards({
  status,
  loading,
}: {
  status: StatusResult | null;
  loading: boolean;
}) {
  const pending = loading && !status;
  const dash = pending ? "Checking..." : "—";
  const online = status?.internet.online;

  const internetAccent = pending
    ? "border-l-slate-300"
    : online
      ? "border-l-ok"
      : "border-l-bad";

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-busy={loading}>
      <Card title="Internet" accent={internetAccent}>
        <p className="flex items-center gap-2 text-xl font-semibold">
          <span
            aria-hidden="true"
            className={`inline-block h-3 w-3 rounded-full ${
              pending ? "bg-slate-300" : online ? "bg-ok" : "bg-bad"
            }`}
          />
          {pending ? "Checking..." : online ? "Online" : "Offline"}
        </p>
        <Line label="Latency" value={status?.internet.online ? fmtMs(status.internet.latency_ms) : dash} />
        <Line
          label="Packet loss"
          value={status?.internet.online ? fmtPercent(status.internet.packet_loss_percent) : dash}
        />
        {status && !status.internet.online && status.internet.message && (
          <p className="pt-1 text-xs text-bad">{status.internet.message}</p>
        )}
      </Card>

      <Card title="Local network" accent="border-l-accent">
        <Line label="Local IP" value={status?.local_ip ?? dash} />
        <Line label="Gateway" value={status ? (status.gateway ?? "Not detected") : dash} />
      </Card>

      <Card title="DNS" accent="border-l-accent">
        <Line label="Server" value={status?.dns_server ?? dash} />
      </Card>

      <Card title="Public IP" accent="border-l-accent">
        <p className="font-mono text-lg">{status ? (status.public_ip ?? "Unavailable") : dash}</p>
        {status && !status.public_ip && (
          <p className="text-xs text-slate-600">The public IP service did not respond.</p>
        )}
      </Card>
    </div>
  );
}
