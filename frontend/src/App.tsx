import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getStatus } from "./api";
import DnsTool from "./components/DnsTool";
import History from "./components/History";
import PingTool from "./components/PingTool";
import PortCheckTool from "./components/PortCheckTool";
import StatusCards from "./components/StatusCards";
import TracerouteTool from "./components/TracerouteTool";
import { ErrorNote } from "./components/ui";
import type { HistoryEntry, HistoryInput, StatusResult } from "./types";

const MAX_HISTORY = 8;

export default function App() {
  const [status, setStatus] = useState<StatusResult | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const nextId = useRef(1);

  const refresh = useCallback(async () => {
    setLoading(true);
    setStatusError(null);
    try {
      setStatus(await getStatus());
    } catch (err) {
      setStatusError(err instanceof ApiError ? err.message : "Could not load the network status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const addHistory = useCallback((entry: HistoryInput) => {
    const id = nextId.current++;
    setHistory((current) => [{ ...entry, id }, ...current].slice(0, MAX_HISTORY));
  }, []);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-wide">NETWORK DIAGNOSTICS</h1>
          <p className="mt-1 text-sm text-slate-600">
            Quick checks for your connection, DNS and route to any host.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={loading}
          className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium hover:border-accent
                     disabled:cursor-wait disabled:opacity-60
                     focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          {loading ? "Checking..." : "Refresh"}
        </button>
      </header>

      {statusError && <ErrorNote message={statusError} />}
      <div className={statusError ? "mt-4" : ""}>
        <StatusCards status={status} loading={loading} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <PingTool onResult={addHistory} />
        <DnsTool onResult={addHistory} />
        <TracerouteTool onResult={addHistory} />
        <PortCheckTool onResult={addHistory} />
      </div>

      <div className="mt-6">
        <History entries={history} onClear={() => setHistory([])} />
      </div>
    </main>
  );
}
