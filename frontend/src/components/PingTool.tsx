import { FormEvent, useState } from "react";
import { runPing } from "../api";
import { fmtMs, fmtPercent } from "../format";
import { useRequest } from "../hooks/useRequest";
import type { HistoryInput, PingResult } from "../types";
import { Badge, ErrorNote, InfoNote, Panel, ResultRows, SubmitButton, TextField } from "./ui";

export default function PingTool({ onResult }: { onResult: (entry: HistoryInput) => void }) {
  const [target, setTarget] = useState("");
  const { data, error, loading, run } = useRequest<PingResult>();

  async function submit(event: FormEvent) {
    event.preventDefault();
    const host = target.trim();
    if (!host) return;
    const result = await run(() => runPing(host));
    if (result) {
      const ok = result.status === "reachable";
      onResult({
        tool: "Ping",
        target: result.host,
        ok,
        summary: ok ? `Ping: ${fmtMs(result.latency_ms)}` : "Ping: unreachable",
      });
    }
  }

  return (
    <Panel title="Ping test" hint="Check whether a host answers and how fast.">
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
        <SubmitButton loading={loading} idle="Test" />
      </form>

      {error && <ErrorNote message={error} />}
      {data && (
        <>
          <ResultRows
            rows={[
              ["Host", data.host],
              [
                "Status",
                <Badge key="s" tone={data.status === "reachable" ? "ok" : "bad"}>
                  {data.status === "reachable" ? "Reachable" : "Unreachable"}
                </Badge>,
              ],
              ["Latency", fmtMs(data.latency_ms)],
              ["Packet loss", data.packets_sent ? fmtPercent(data.packet_loss_percent) : "—"],
            ]}
          />
          {data.message && <InfoNote message={data.message} />}
        </>
      )}
    </Panel>
  );
}
