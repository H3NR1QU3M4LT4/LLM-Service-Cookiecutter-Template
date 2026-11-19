# Frontend UI (shared look)

`apps/frontend` and `apps/evals/dashboard` look the same: same Leica logo, navbar, footer, content margins and
colour tokens, so every Leica app feels like one product.

| Shared file | What |
|---|---|
| `src/layout/AppShell.tsx` | Page chrome: navbar, centred column (`max-w-6xl`, `px-4 sm:px-6 lg:px-8`, `py-6`, `space-y-5`), footer |
| `src/layout/Navbar.tsx` | Logo, app title, section links, right slot; height `h-16` |
| `src/layout/Footer.tsx` | Copyright, and the **environment badge and version** of the app you are looking at |
| `src/layout/brand.ts` | Logo and name per brand (`lms` Leica Microsystems, `lbs` Leica Biosystems) and the default brand |
| `src/index.css` | Tailwind theme (`leica-*` colours, Univers font), `btn-primary`, `btn-ghost`, `card`, `badge`, inputs |
| `src/assets/*.png`, `public/favicon.ico` | Both brand logos and the favicon |

The footer shows `vX.Y.Z` and `LOCAL|DEV|UAT|PROD`. In `apps/frontend` both come from the backend's `/status`
(`APP_VERSION`, `ENVIRONMENT`), so the version is the backend's; the evals dashboard is a local tool and shows
`local`.

## Brand: Leica Microsystems (LMS) or Leica Biosystems (LBS)

The cookiecutter question `brand` (`lms` or `lbs`) decides the logo in the navbar and the name in the footer
("© 2026 Leica Microsystems" or "Leica Biosystems") for both apps. The post-generation hook writes the choice as
`DEFAULT_BRAND` in `src/layout/brand.ts` and as the `VITE_BRAND` default of `apps/frontend/Dockerfile`.

Both logos ship in `src/assets` (`leica-microsystems.png`, `leica-biosystems.png`), so switching later is one line:
change `DEFAULT_BRAND` in both `brand.ts` files, or build with `VITE_BRAND=lbs` (`docker build --build-arg
VITE_BRAND=lbs`). Replace a logo by overwriting its PNG in both apps.

## Tab title and icon

The browser tab reads `<project name> · <brand>` (`AppShell` sets `document.title`; `index.html` carries the project
name for the instant before the app loads, the evals dashboard adds " Evals"). The post-generation hook writes the
project name into both. The tab icon is a white "Leica" on a red rounded square (`public/favicon.ico`, `favicon.png`,
`apple-touch-icon.png`), the same for both brands.

## Keeping them identical

The files above are copies. `scripts/check-ui-sync.sh` fails (pre-commit hook `ui-sync`, so also in CI) when any of
them differs between the two apps. Change both together; if a third frontend appears, move them to an npm workspace
package instead of copying again.
