import { FormEvent, useState } from "react";
import { checkPort } from "../api";
import { fmtMs } from "../format";
import { useRequest } from "../hooks/useRequest";
import type { HistoryInput, PortCheckResult } from "../types";
import { Badge, ErrorNote, InfoNote, Panel, ResultRows, SubmitButton, TextField } from "./ui";

const LABEL: Record<PortCheckResult["status"], string> = {
  open: "OPEN",
  closed: "CLOSED",
  timeout: "TIMEOUT",
  error: "ERROR",
};

export default function PortCheckTool({ onResult }: { onResult: (entry: HistoryInput) => void }) {
  const [host, setHost] = useState("");
  const [port, setPort] = useState("");
  const { data, error, loading, run, fail } = useRequest<PortCheckResult>();

  async function submit(event: FormEvent) {
    event.preventDefault();
    const name = host.trim();
    const portNumber = Number(port);
    if (!name || !port.trim()) return;
    if (!Number.isInteger(portNumber) || portNumber < 1 || portNumber > 65535) {
      fail("Port must be a number between 1 and 65535.");
      return;
    }
    const result = await run(() => checkPort(name, portNumber));
    if (result) {
      onResult({
        tool: "Port",
        target: `${result.host}:${result.port}`,
        ok: result.status === "open",
        summary: `Port ${result.port}: ${LABEL[result.status]}`,
      });
    }
  }

  return (
    <Panel title="Port check" hint="Test one TCP port on one host. This is not a port scanner.">
      <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
        <TextField
          label="Host"
          className="min-w-[10rem] flex-1"
          placeholder="192.168.1.1"
          value={host}
          onChange={(e) => setHost(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        <TextField
          label="Port"
          className="w-24"
          placeholder="80"
          inputMode="numeric"
          value={port}
          onChange={(e) => setPort(e.target.value)}
          autoComplete="off"
        />
        <SubmitButton loading={loading} idle="Check" busy="Checking..." />
      </form>

      {error && <ErrorNote message={error} />}
      {data && (
        <>
          <ResultRows
            rows={[
              ["Host", data.host],
              [
                `Port ${data.port}`,
                <Badge key="s" tone={data.status === "open" ? "ok" : data.status === "error" ? "warn" : "bad"}>
                  {LABEL[data.status]}
                </Badge>,
              ],
              ["Response time", fmtMs(data.response_time_ms)],
            ]}
          />
          {data.message && <InfoNote message={data.message} />}
        </>
      )}
    </Panel>
  );
}
