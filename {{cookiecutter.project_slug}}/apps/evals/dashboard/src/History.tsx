import { type Run, summarize } from "./data";
import { num, pct, usd, when } from "./format";

/** Same variant across runs: did a change help? Newest run first. */
export default function History({ runs }: { runs: Run[] }) {
  const variants = [...new Set(runs.flatMap((r) => r.variants.map((v) => v.id)))].sort();
  return (
    <section className="space-y-4">
      <h2 className="page-title">History</h2>
      {variants.map((id) => (
        <div key={id} className="card overflow-x-auto p-0">
          <p className="border-b border-gray-200 bg-gray-50 px-4 py-2 font-mono text-xs">{id}</p>
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-gray-500">
              <tr>
                {["Run", "When", "Commit", "Dataset", "Checks passed", "Judge", "Latency p95 ms", "Cost"].map((h) => (
                  <th key={h} className="px-4 py-2 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {runs
                .filter((r) => r.variants.some((v) => v.id === id))
                .map((r) => {
                  const s = summarize(r.rows, id);
                  return (
                    <tr key={r.run_id} className="border-t border-gray-100">
                      <td className="px-4 py-2">{r.label}</td>
                      <td className="px-4 py-2">{when(r.created_at)}</td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {r.git_commit ?? "–"}
                        {r.git_dirty ? "*" : ""}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs">{r.dataset.sha256}</td>
                      <td className="px-4 py-2">{pct(s.passRate)}</td>
                      <td className="px-4 py-2">{num(s.judge, 2)}</td>
                      <td className="px-4 py-2">{num(s.p95)}</td>
                      <td className="px-4 py-2">{usd(s.cost)}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      ))}
      <p className="text-xs text-gray-500">Scores are only comparable on the same dataset hash and judge version.</p>
    </section>
  );
}
