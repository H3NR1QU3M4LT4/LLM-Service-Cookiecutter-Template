import { useEffect, useState } from "react";

import Cases from "./Cases";
import Comparison from "./Comparison";
import { type Run, loadRuns } from "./data";
import { when } from "./format";
import History from "./History";
import AppShell from "./layout/AppShell";

const NAV = [
  { key: "comparison", label: "Comparison" },
  { key: "cases", label: "Cases" },
  { key: "history", label: "History" },
];

export default function App() {
  const [runs, setRuns] = useState<Run[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState("comparison");
  const [runId, setRunId] = useState("");
  const [baseline, setBaseline] = useState("");

  useEffect(() => {
    loadRuns().then(
      (loaded) => {
        setRuns(loaded);
        setRunId(loaded[0]?.run_id ?? "");
      },
      (e: Error) => setError(e.message),
    );
  }, []);

  const run = runs?.find((r) => r.run_id === runId);

  return (
    <AppShell
      title="LLM Evals"
      navItems={NAV}
      activeNav={view}
      onNavSelect={setView}
      footerVersion={import.meta.env.VITE_APP_VERSION ?? "dev"}
      footerEnvironment="local"
    >
      {error && (
        <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          No results yet ({error}). Run: <code>uv run python -m evals run --models ollama:gemma4:e2b</code>
        </p>
      )}
      {runs && !runs.length && <p className="text-sm text-gray-500">No runs in results/ yet.</p>}
      {runs && run && (
        <>
          {view !== "history" && (
            <label className="flex items-center gap-2 text-sm text-gray-600">
              Run
              <select
                className="select-field"
                value={runId}
                onChange={(e) => {
                  setRunId(e.target.value);
                  setBaseline("");
                }}
              >
                {runs.map((r) => (
                  <option key={r.run_id} value={r.run_id}>
                    {r.label} · {when(r.created_at)}
                  </option>
                ))}
              </select>
            </label>
          )}
          {view === "comparison" && <Comparison run={run} baseline={baseline} onBaseline={setBaseline} />}
          {view === "cases" && <Cases key={run.run_id} run={run} />}
          {view === "history" && <History runs={runs} />}
        </>
      )}
    </AppShell>
  );
}
