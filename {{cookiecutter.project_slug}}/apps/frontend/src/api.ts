export type Environment = "local" | "dev" | "uat" | "prod";

export interface Status {
  status: "ok";
  service: string;
  version: string;
  environment: Environment;
  providers: { name: string; model: string; role: "primary" | "fallback" }[];
}

export interface Ask {
  result: { answer: string; confidence: number };
  provider: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${response.status}`);
  }
  return response.json();
}

export const getStatus = () => request<Status>("/status");

export const ask = (question: string) =>
  request<Ask>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
