import type { InputHTMLAttributes, ReactNode } from "react";

export function Panel({
  title,
  hint,
  children,
}: {
  title: string;
  hint: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-line bg-white p-5">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-1 text-sm text-slate-600">{hint}</p>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function TextField({
  label,
  className = "",
  ...props
}: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1 block text-sm font-medium">{label}</span>
      <input
        {...props}
        className="w-full rounded-md border border-line bg-white px-3 py-2 font-mono text-sm
                   placeholder:text-slate-400 focus:border-accent focus:outline-none
                   focus-visible:ring-2 focus-visible:ring-accent/30"
      />
    </label>
  );
}

export function SubmitButton({
  loading,
  idle,
  busy = "Testing...",
}: {
  loading: boolean;
  idle: string;
  busy?: string;
}) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white
                 hover:bg-blue-700 disabled:cursor-wait disabled:opacity-60
                 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2
                 focus-visible:outline-accent"
    >
      {loading ? busy : idle}
    </button>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <p
      role="alert"
      className="mt-4 rounded-md border border-bad/30 bg-red-50 px-3 py-2 text-sm text-bad"
    >
      {message}
    </p>
  );
}

export function InfoNote({ message }: { message: string }) {
  return (
    <p className="mt-3 rounded-md border border-warn/30 bg-amber-50 px-3 py-2 text-sm text-warn">
      {message}
    </p>
  );
}

type Tone = "ok" | "bad" | "warn" | "neutral";

const toneClass: Record<Tone, string> = {
  ok: "bg-emerald-50 text-ok",
  bad: "bg-red-50 text-bad",
  warn: "bg-amber-50 text-warn",
  neutral: "bg-slate-100 text-slate-700",
};

export function Badge({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-sm font-medium ${toneClass[tone]}`}>
      {children}
    </span>
  );
}

export function ResultRows({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <dl className="mt-4 divide-y divide-line rounded-md border border-line">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-start justify-between gap-4 px-3 py-2 text-sm">
          <dt className="text-slate-600">{label}</dt>
          <dd className="text-right font-mono">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
