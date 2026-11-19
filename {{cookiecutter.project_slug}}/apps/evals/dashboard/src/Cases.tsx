import { useState } from "react";

import type { Row, Run } from "./data";

function Answer({ row }: { row: Row | undefined }) {
  if (!row) return <p className="text-sm text-gray-400">No result.</p>;
  return (
    <div className="space-y-2 text-sm">
      <p className="font-mono text-xs text-gray-500">{row.variant}</p>
      {row.error ? <p className="text-leica-700">{row.error}</p> : <p className="whitespace-pre-wrap">{row.output}</p>}
      <div className="flex flex-wrap gap-1">
        {Object.entries(row.checks).map(([name, ok]) => (
          <span key={name} className={`badge ${ok ? "bg-green-100 text-green-800" : "bg-leica-100 text-leica-800"}`}>
            {name}
          </span>
        ))}
        {row.judge_score !== null && <span className="badge bg-gray-200 text-gray-800">judge {row.judge_score}/5</span>}
      </div>
      {row.judge_reason && <p className="text-gray-600">{row.judge_reason}</p>}
      <p className="text-xs text-gray-500">
        {row.latency_ms ?? "–"} ms · {row.input_tokens ?? "–"} in / {row.output_tokens ?? "–"} out tokens
      </p>
    </div>
  );
}

const severity = (row: Row | undefined) => (row ? (row.passed ? 0 : 10) + (5 - (row.judge_score ?? 5)) : 0);

export default function Cases({ run }: { run: Run }) {
  const [variant, setVariant] = useState(run.variants[0]?.id ?? "");
  const [other, setOther] = useState("");
  const [onlyFailing, setOnlyFailing] = useState(false);

  const byCase = (id: string) => (v: string) => run.rows.find((r) => r.case_id === id && r.variant === v);
  const ids = [...new Set(run.rows.map((r) => r.case_id))]
    .filter((id) => !onlyFailing || severity(byCase(id)(variant)) > 0)
    .sort((a, b) => severity(byCase(b)(variant)) - severity(byCase(a)(variant)));

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <h2 className="page-title">Cases</h2>
        <select className="select-field" value={variant} onChange={(e) => setVariant(e.target.value)}>
          {run.variants.map((v) => (
            <option key={v.id}>{v.id}</option>
          ))}
        </select>
        <select className="select-field" value={other} onChange={(e) => setOther(e.target.value)}>
          <option value="">Compare with…</option>
          {run.variants
            .filter((v) => v.id !== variant)
            .map((v) => (
              <option key={v.id}>{v.id}</option>
            ))}
        </select>
        <label className="ml-auto flex items-center gap-2 text-gray-600">
          <input type="checkbox" checked={onlyFailing} onChange={(e) => setOnlyFailing(e.target.checked)} />
          Only failing or low score
        </label>
      </div>
      {ids.map((id) => {
        const row = byCase(id)(variant);
        return (
          <article key={id} className="card space-y-3">
            <header>
              <p className="font-mono text-xs text-gray-500">{id}</p>
              <p className="font-medium">{row?.question}</p>
            </header>
            <div className={`grid gap-4 ${other ? "md:grid-cols-2" : ""}`}>
              <Answer row={row} />
              {other && <Answer row={byCase(id)(other)} />}
            </div>
          </article>
        );
      })}
      {!ids.length && <p className="text-sm text-gray-500">Nothing to show.</p>}
    </section>
  );
}
