---
name: testing-vvaharness-console
description: How to run and browser-test the vvaharness-console web app (FastAPI + React/Vite) locally.
---

# Testing vvaharness-console

## Start services (from repo root /home/ubuntu/repos/vvaharness-console)
- Backend: `./.venv/bin/uvicorn backend.app.main:app --port 8000` (health check: `curl http://localhost:8000/api/health`)
- Frontend: `cd frontend && npm run dev` → Vite on port 5173, proxies `/api` to :8000.

## Gotcha: Vite may bind IPv6-only
Vite dev server can bind only to `[::1]:5173`. Chrome may then fail on `http://localhost:5173` with ERR_CONNECTION_REFUSED even though curl works. Workaround: open `http://[::1]:5173/` in the browser instead (or start vite with `--host 127.0.0.1`).

## App structure / test hooks
- SPA routes: `/` Dashboard, `/scans`, `/scans/:id`, `/findings`, `/targets`, `/settings` (frontend/src/App.tsx).
- Settings: link provider (kind anthropic/openai/google + API key). With an invalid key the provider is still created with status "invalid" — this is expected behavior, not an error. `last_verified_at` is only set on successful verification (backend/app/routers/providers.py).
- Scans: selecting a provider immediately fetches `/api/providers/{id}/models`; with an invalid key this shows a red inline error like "Could not list models: openai API returned 401" — expected.
- Runtime data (SQLite DB, Fernet key) lives in `data/` (gitignored). To reset state, delete rows via UI or remove `data/console.db` and restart uvicorn.
- Real scans require a valid provider API key and spend tokens — avoid starting scans in tests unless explicitly requested.

## Devin Secrets Needed
- None for UI golden paths. A valid ANTHROPIC/OPENAI/GEMINI API key would be needed to test provider verification success, live model listing, and real scans.
