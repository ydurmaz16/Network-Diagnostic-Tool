import { FormEvent, useState } from "react";
import { runDns } from "../api";
import { fmtMs } from "../format";
import { useRequest } from "../hooks/useRequest";
import type { DnsResult, HistoryInput } from "../types";
import { Badge, ErrorNote, InfoNote, Panel, ResultRows, SubmitButton, TextField } from "./ui";

export default function DnsTool({ onResult }: { onResult: (entry: HistoryInput) => void }) {
  const [hostname, setHostname] = useState("");
  const { data, error, loading, run } = useRequest<DnsResult>();

  async function submit(event: FormEvent) {
    event.preventDefault();
    const name = hostname.trim();
    if (!name) return;
    const result = await run(() => runDns(name));
    if (result) {
      const ok = result.status === "resolved";
      onResult({
        tool: "DNS",
        target: result.hostname,
        ok,
        summary: ok ? `DNS: ${fmtMs(result.response_time_ms)}` : "DNS: failed",
      });
    }
  }

  return (
    <Panel title="DNS lookup" hint="See which IP addresses a hostname points to.">
      <form onSubmit={submit} className="flex items-end gap-3">
        <TextField
          label="Hostname"
          className="flex-1"
          placeholder="google.com"
          value={hostname}
          onChange={(e) => setHostname(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        <SubmitButton loading={loading} idle="Look up" busy="Looking up..." />
      </form>

      {error && <ErrorNote message={error} />}
      {data && (
        <>
          <ResultRows
            rows={[
              ["Hostname", data.hostname],
              [
                "Status",
                <Badge key="s" tone={data.status === "resolved" ? "ok" : "bad"}>
                  {data.status === "resolved" ? "Resolved" : "Failed"}
                </Badge>,
              ],
              ["DNS server", data.dns_server ?? "—"],
              ["Response time", fmtMs(data.response_time_ms)],
              [
                "Addresses",
                data.addresses.length ? (
                  <ul key="a">
                    {data.addresses.map((address) => (
                      <li key={address}>{address}</li>
                    ))}
                  </ul>
                ) : (
                  "—"
                ),
              ],
            ]}
          />
          {data.message && <InfoNote message={data.message} />}
        </>
      )}
    </Panel>
  );
}
