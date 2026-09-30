import type { HistoryEntry } from "../types";

export default function History({
  entries,
  onClear,
}: {
  entries: HistoryEntry[];
  onClear: () => void;
}) {
  return (
    <section className="rounded-lg border border-line bg-white p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Recent tests</h2>
        {entries.length > 0 && (
          <button
            type="button"
            onClick={onClear}
            className="text-sm text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          >
            Clear
          </button>
        )}
      </div>

      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">
          Run a test above and the result will show up here. History is cleared when you reload the page.
        </p>
      ) : (
        <ul className="mt-3 divide-y divide-line">
          {entries.map((entry) => (
            <li key={entry.id} className="flex items-center justify-between gap-4 py-2 text-sm">
              <span className="font-mono">{entry.target}</span>
              <span className="flex items-center gap-3">
                <span className="text-slate-600">{entry.summary}</span>
                <span
                  className={entry.ok ? "text-ok" : "text-bad"}
                  role="img"
                  aria-label={entry.ok ? "Success" : "Failed"}
                >
                  {entry.ok ? "✓" : "✗"}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
