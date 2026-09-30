import { FormEvent, useState } from "react";
import { runTraceroute } from "../api";
import { fmtMs } from "../format";
import { useRequest } from "../hooks/useRequest";
import type { HistoryInput, TracerouteResult } from "../types";
import { ErrorNote, InfoNote, Panel, SubmitButton, TextField } from "./ui";

export default function TracerouteTool({ onResult }: { onResult: (entry: HistoryInput) => void }) {
  const [target, setTarget] = useState("");
  const { data, error, loading, run } = useRequest<TracerouteResult>();

  async function submit(event: FormEvent) {
    event.preventDefault();
    const host = target.trim();
    if (!host) return;
    const result = await run(() => runTraceroute(host));
    if (result) {
      const ok = result.status !== "failed";
      onResult({
        tool: "Traceroute",
        target: result.target,
        ok,
        summary: ok ? `Traceroute: ${result.hops.length} hops` : "Traceroute: failed",
      });
    }
  }

  return (
    <Panel title="Traceroute" hint="Follow the route your traffic takes. This can take up to a minute.">
      <form onSubmit={submit} className="flex items-end gap-3">
        <TextField
          label="Hostname or IP"
          className="flex-1"
          placeholder="google.com"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        <SubmitButton loading={loading} idle="Run traceroute" busy="Tracing..." />
      </form>

      {error && <ErrorNote message={error} />}
      {data && data.hops.length > 0 && (
        <div className="mt-4 max-h-80 overflow-auto rounded-md border border-line">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-slate-50 text-slate-600">
              <tr>
                <th className="px-3 py-2 font-medium">Hop</th>
                <th className="px-3 py-2 font-medium">Address</th>
                <th className="px-3 py-2 text-right font-medium">Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line font-mono">
              {data.hops.map((hop) => (
                <tr key={hop.hop}>
                  <td className="px-3 py-1.5">{hop.hop}</td>
                  <td className="px-3 py-1.5">
                    {hop.address ?? <span className="text-slate-500">No response</span>}
                  </td>
                  <td className="px-3 py-1.5 text-right">{fmtMs(hop.latency_ms)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data?.message && (data.status === "failed" ? <ErrorNote message={data.message} /> : <InfoNote message={data.message} />)}
    </Panel>
  );
}
