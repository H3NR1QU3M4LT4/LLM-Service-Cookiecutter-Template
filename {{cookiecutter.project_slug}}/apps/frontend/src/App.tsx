import { useEffect, useState } from "react";

import { type Ask, type Status, ask, getStatus } from "./api";
import AppShell from "./layout/AppShell";

function useStatus() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getStatus().then(setStatus, (e: Error) => setError(e.message));
  }, []);
  return { status, error };
}

export default function App() {
  const { status, error: statusError } = useStatus();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Ask | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setAnswer(await ask(question));
    } catch (e) {
      setAnswer(null);
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell
      title="LLM Service"
      footerVersion={status?.version}
      footerEnvironment={status?.environment}
      footerInfo={status ? status.providers.map((p) => `${p.role}: ${p.name} · ${p.model}`).join("  |  ") : undefined}
    >
      {statusError && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">API unreachable: {statusError}</p>}

      <h1 className="page-title">Ask</h1>
      <form onSubmit={submit} className="space-y-3">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          maxLength={4000}
          rows={4}
          required
          placeholder="Ask something…"
          className="input-field"
        />
        <button type="submit" disabled={loading || !question.trim()} className="btn-primary">
          {loading ? "Asking…" : "Ask"}
        </button>
      </form>

      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}

      {answer && (
        <section className="card space-y-2">
          <p>{answer.result.answer}</p>
          <p className="text-sm text-gray-500">
            confidence {Math.round(answer.result.confidence * 100)}% · via {answer.provider}
          </p>
        </section>
      )}
    </AppShell>
  );
}
