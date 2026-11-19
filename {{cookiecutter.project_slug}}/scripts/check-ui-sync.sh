#!/usr/bin/env bash
# The frontends share one look: logo, navbar, footer, margins and Leica tokens. Fail when the shared files differ.
set -euo pipefail
cd "$(dirname "$0")/.."
A=apps/frontend
B=apps/evals/dashboard
status=0
for path in src/layout src/index.css src/assets/leica-microsystems.png public/favicon.ico; do
  if ! diff -r "$A/$path" "$B/$path" >/dev/null; then
    echo "UI drift: $A/$path and $B/$path differ. Change both (see docs/frontend-ui.md)." >&2
    status=1
  fi
done
exit $status
