# Frontend

React 19 + Vite + TypeScript + Tailwind CSS 4. Shows the API's `/status` (service, version, environment, providers)
and a form that calls `POST /ask`.

## Run locally

```bash
npm install
npm run dev          # http://localhost:5173
```

The app only calls `/api/*`. In dev Vite proxies it to `http://localhost:8000` (the backend, run `uvicorn` first);
set `BACKEND_URL` to point elsewhere. The backend needs no `API_KEY` when `ENVIRONMENT=local`.

## Docker

```bash
docker build -t frontend .
docker run -p 8080:8080 -e BACKEND_URL=http://host.docker.internal:8000 -e API_KEY=change-me frontend
```

nginx serves the build on port 8080 and proxies `/api/` to `BACKEND_URL`, adding the `X-API-Key` header from `API_KEY`
at container start. The key is never in the JS bundle. `package-lock.json` must be committed (`npm ci`).

| Variable | Default | Meaning |
|---|---|---|
| `BACKEND_URL` | `http://api:8000` | Backend base URL with scheme (`https://...azurewebsites.net` on Azure) |
| `API_KEY` | empty | Sent to the backend as `X-API-Key` |

## Look

The shell (logo, navbar, footer with version and environment, margins) is shared with `apps/evals/dashboard`; see
[docs/frontend-ui.md](../../docs/frontend-ui.md). Edit both together: a pre-commit hook enforces it.

## Layout

| Path | What |
|---|---|
| `src/api.ts` | Typed fetch client for `/status` and `/ask` |
| `src/App.tsx` | Status bar (version, environment badge, providers) and ask form |
| `nginx.conf.template` | Static hosting, SPA fallback, `/api/` proxy |
