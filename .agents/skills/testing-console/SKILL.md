---
name: testing-vvaharness-console
description: How to run and browser-test the vvaharness-console web app (FastAPI + React/Vite) locally.
---

# Testing vvaharness-console

## Start services (from repo root /home/ubuntu/repos/vvaharness-console)
- Preferred: `bash start.sh` (installs backend+frontend, starts uvicorn :8000 in background + Vite on 127.0.0.1:5173 in foreground; Ctrl+C stops both via trap). Run it in a persistent tty shell so you can Ctrl+C later.
- Manual alternative: `./.venv/bin/uvicorn backend.app.main:app --port 8000` and `cd frontend && npm run dev` (health check: `curl http://localhost:8000/api/health`).

## Gotcha: Vite may bind IPv6-only
Vite dev server can bind only to `[::1]:5173`. Chrome may then fail on `http://localhost:5173` with ERR_CONNECTION_REFUSED even though curl works. Workaround: open `http://[::1]:5173/` in the browser instead (or start vite with `--host 127.0.0.1`).

## App structure / test hooks
- SPA routes: `/` Dashboard, `/scans`, `/scans/:id`, `/findings`, `/targets`, `/settings` (frontend/src/App.tsx).
- Settings: link provider (kind anthropic/openai/google + API key). With an invalid key the provider is still created with status "invalid" — this is expected behavior, not an error. `last_verified_at` is only set on successful verification (backend/app/routers/providers.py).
- Scans: selecting a provider immediately fetches `/api/providers/{id}/models`; with an invalid key this shows a red inline error like "Could not list models: openai API returned 401" — expected.
- Runtime data (SQLite DB, Fernet key) lives in `data/` (gitignored). To reset state, delete rows via UI or remove `data/console.db` and restart uvicorn.
- Real scans require a valid provider API key and spend tokens — avoid starting scans in tests unless explicitly requested.

## Testing the "custom" (OpenAI-compatible) provider without credentials
- Settings has a 4th provider kind "Custom (OpenAI-compatible)": base URL required (Link button disabled without it), API key optional. Backend rejects kind=custom without base_url with HTTP 400.
- Success path is testable with a tiny mock server: serve GET /v1/models returning `{"data":[{"id":"..."}]}` on a local port and use `http://127.0.0.1:<port>/v1` as base URL — the provider verifies "verified" and its models appear in the Scans model dropdown. With empty key the backend sends no Authorization header (log it in the mock to confirm).
- Gotcha: when killing/restarting a mock started via `bash -c "... mock_openai.py ..."`, `pkill -f mock_openai` matches your own wrapper shell and kills it (exit -1). Use `ps aux | grep mock_openai | awk '{print $2}' | xargs kill` or launch via a separate starter script.
- Use `python3 -u` (unbuffered) for mock servers whose logs you want to read while they run; nohup buffering otherwise hides output.

## Devin Secrets Needed
- None for UI golden paths. A valid ANTHROPIC/OPENAI/GEMINI API key would be needed to test provider verification success, live model listing, and real scans.
