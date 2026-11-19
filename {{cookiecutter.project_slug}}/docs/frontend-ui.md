# Frontend UI (shared look)

`apps/frontend` and `apps/evals/dashboard` look the same: same Leica logo, navbar, footer, content margins and
colour tokens, so every Leica app feels like one product.

| Shared file | What |
|---|---|
| `src/layout/AppShell.tsx` | Page chrome: navbar, centred column (`max-w-6xl`, `px-4 sm:px-6 lg:px-8`, `py-6`, `space-y-5`), footer |
| `src/layout/Navbar.tsx` | Logo, app title, section links, right slot; height `h-16` |
| `src/layout/Footer.tsx` | Copyright, and the **environment badge and version** of the app you are looking at |
| `src/layout/brand.ts` | Logo and name per brand (`lms` Leica Microsystems, `lbs` Leica Biosystems) |
| `src/index.css` | Tailwind theme (`leica-*` colours, Univers font), `btn-primary`, `btn-ghost`, `card`, `badge`, inputs |
| `src/assets/leica-microsystems.png`, `public/favicon.ico` | Logo and favicon |

The footer shows `vX.Y.Z` and `LOCAL|DEV|UAT|PROD`. In `apps/frontend` both come from the backend's `/status`
(`APP_VERSION`, `ENVIRONMENT`), so the version is the backend's; the evals dashboard is a local tool and shows
`local`.

## Brand

`VITE_BRAND=lms|lbs` at build time picks the brand (default `lms`); the Docker build takes it as a build argument.
The Leica Biosystems logo is not in the template (no asset was available). Add it as
`src/assets/leica-biosystems.png` or `.svg` in both apps; `brand.ts` picks it up with no code change. Until then `lbs`
shows a red LEICA wordmark.

## Keeping them identical

The files above are copies. `scripts/check-ui-sync.sh` fails (pre-commit hook `ui-sync`, so also in CI) when any of
them differs between the two apps. Change both together; if a third frontend appears, move them to an npm workspace
package instead of copying again.
