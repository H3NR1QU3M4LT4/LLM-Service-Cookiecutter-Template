import fs from "node:fs";
import type { IncomingMessage, ServerResponse } from "node:http";
import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

// Serves ../results (written by `python -m evals run`) at /results/*, so the dashboard needs no API.
function serveResults(): Plugin {
  const dir = path.resolve(process.env.EVALS_RESULTS_DIR ?? path.join(__dirname, "../results"));
  const handler = (req: IncomingMessage, res: ServerResponse, next: () => void) => {
    if (!req.url?.startsWith("/results/")) return next();
    const file = path.resolve(dir, decodeURIComponent(req.url.slice("/results/".length).split("?")[0]));
    if (!file.startsWith(dir + path.sep) || !fs.existsSync(file)) {
      res.statusCode = 404;
      return res.end();
    }
    res.setHeader("Content-Type", "application/json");
    fs.createReadStream(file).pipe(res);
  };
  return {
    name: "serve-results",
    configureServer: (server) => void server.middlewares.use(handler),
    configurePreviewServer: (server) => void server.middlewares.use(handler),
  };
}

export default defineConfig({ plugins: [react(), tailwindcss(), serveResults()] });
