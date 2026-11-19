import { type Run, summarize } from "./data";
import { delta, num, pct, usd } from "./format";

function Bar({ value, max }: { value: number | null; max: number }) {
  return (
    <div className="mt-1 h-1.5 w-full rounded bg-gray-100">
      <div className="h-1.5 rounded bg-leica-600" style={{ width: `${max && value ? (value / max) * 100 : 0}%` }} />
    </div>
  );
}

function Delta({ d }: { d: ReturnType<typeof delta> }) {
  return d ? <span className={`ml-1 text-xs ${d.color}`}>{d.text}</span> : null;
}

export default function Comparison({
  run,
  baseline,
  onBaseline,
}: {
  run: Run;
  baseline: string;
  onBaseline: (variant: string) => void;
}) {
  const summaries = run.variants.map((v) => summarize(run.rows, v.id));
  const base = summaries.find((s) => s.variant === baseline) ?? summaries[0];
  const maxP95 = Math.max(...summaries.map((s) => s.p95 ?? 0));

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <h2 className="page-title">Comparison</h2>
        <label className="ml-auto flex items-center gap-2 text-gray-600">
          Baseline
          <select className="select-field" value={base?.variant} onChange={(e) => onBaseline(e.target.value)}>
            {run.variants.map((v) => (
              <option key={v.id}>{v.id}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
            <tr>
              {["Variant", "Cases", "Checks passed", "Errors", "Judge (1-5)", "Latency p50 ms", "Latency p95 ms", "Tokens in / out", "Cost"].map(
                (h) => (
                  <th key={h} className="px-4 py-3 font-semibold">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {summaries.map((s) => (
              <tr key={s.variant} className="border-b border-gray-100 last:border-0">
                <td className="px-4 py-3 font-mono text-xs">{s.variant}</td>
                <td className="px-4 py-3">{s.cases}</td>
                <td className="px-4 py-3">
                  {pct(s.passRate)}
                  <Delta d={delta(s.passRate * 100, base.passRate * 100, true, 0)} />
                </td>
                <td className="px-4 py-3">{pct(s.errorRate)}</td>
                <td className="px-4 py-3">
                  {num(s.judge, 2)}
                  <Delta d={delta(s.judge, base.judge, true)} />
                  <Bar value={s.judge} max={5} />
                </td>
                <td className="px-4 py-3">
                  {num(s.p50)}
                  <Delta d={delta(s.p50, base.p50, false, 0)} />
                </td>
                <td className="px-4 py-3">
                  {num(s.p95)}
                  <Delta d={delta(s.p95, base.p95, false, 0)} />
                  <Bar value={s.p95} max={maxP95} />
                </td>
                <td className="px-4 py-3">
                  {num(s.avgInput)} / {num(s.avgOutput)}
                </td>
                <td className="px-4 py-3">{usd(s.cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-500">
        Deltas are against the baseline row (green = better). Judge{" "}
        {run.judge ? `${run.judge.model}, prompt v${run.judge.prompt_version}` : "not used in this run"}; temperature{" "}
        {run.temperature}; dataset {run.dataset.path} ({run.dataset.sha256}, {run.dataset.cases} cases); commit{" "}
        {run.git_commit ?? "–"}
        {run.git_dirty ? " (uncommitted changes)" : ""}.
      </p>
    </section>
  );
}
