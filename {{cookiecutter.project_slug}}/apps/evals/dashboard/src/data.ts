export interface Row {
  variant: string;
  case_id: string;
  question: string;
  output: string | null;
  error: string | null;
  checks: Record<string, boolean>;
  passed: boolean;
  judge_score: number | null;
  judge_reason: string | null;
  latency_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number | null;
}

export interface Run {
  run_id: string;
  label: string;
  created_at: string;
  git_commit: string | null;
  git_dirty: boolean;
  dataset: { path: string; sha256: string; cases: number };
  temperature: number;
  judge: { model: string; prompt_version: string } | null;
  variants: { id: string; provider: string; model: string; prompt: string; prompt_version: string }[];
  rows: Row[];
}

export interface IndexEntry {
  run_id: string;
  label: string;
  created_at: string;
  variants: string[];
  cases: number;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

/** Every run listed in results/index.json (newest first). */
export async function loadRuns(): Promise<Run[]> {
  const index = await getJson<IndexEntry[]>("/results/index.json");
  return Promise.all(index.map((entry) => getJson<Run>(`/results/runs/${entry.run_id}.json`)));
}

export interface Summary {
  variant: string;
  cases: number;
  passRate: number;
  errorRate: number;
  judge: number | null;
  p50: number | null;
  p95: number | null;
  avgInput: number | null;
  avgOutput: number | null;
  cost: number | null;
}

const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);

function percentile(xs: number[], p: number): number | null {
  if (!xs.length) return null;
  const sorted = [...xs].sort((a, b) => a - b);
  return sorted[Math.min(sorted.length - 1, Math.ceil((p / 100) * sorted.length) - 1)];
}

const present = (xs: (number | null)[]): number[] => xs.filter((x): x is number => x !== null);

export function summarize(rows: Row[], variant: string): Summary {
  const own = rows.filter((r) => r.variant === variant);
  const costs = present(own.map((r) => r.cost_usd));
  const latencies = present(own.map((r) => r.latency_ms));
  return {
    variant,
    cases: own.length,
    passRate: own.filter((r) => r.passed).length / (own.length || 1),
    errorRate: own.filter((r) => r.error).length / (own.length || 1),
    judge: mean(present(own.map((r) => r.judge_score))),
    p50: percentile(latencies, 50),
    p95: percentile(latencies, 95),
    avgInput: mean(present(own.map((r) => r.input_tokens))),
    avgOutput: mean(present(own.map((r) => r.output_tokens))),
    cost: costs.length ? costs.reduce((a, b) => a + b, 0) : null,
  };
}
