# vvaharness console

A web console around the [Visa Vulnerability Agentic Harness](https://github.com/visa/visa-vulnerability-agentic-harness) (`vvaharness`) CLI. It never modifies the harness itself — it orchestrates the released tool as a subprocess and ingests its SARIF output.

Features:

- **Provider linking** — add Anthropic, OpenAI, or Google (Gemini) API keys, or a custom OpenAI-compatible endpoint (Ollama, Groq, OpenRouter, Hugging Face router, …); keys are verified against the provider's model API and stored encrypted at rest (Fernet).
- **Model selection** — models are listed live from the linked provider; pick the one used for the scan's detection roles.
- **Targets** — register scan targets by git URL or local path.
- **Scans** — detection-only runs (`--stop-after s9`, remediation/validation disabled) with cost estimate, live status, and streamed logs.
- **Findings & triage** — SARIF findings ingested into SQLite with triage states (open / confirmed / false positive / accepted risk / fixed).
- **Dashboard** — scan and finding metrics, severity/CWE breakdowns, trends.

> Findings are LLM-generated triage candidates, not confirmed vulnerabilities. Scans spend real model tokens — the console runs `vvaharness estimate` before each scan. Only scan code you are authorized to scan.

## Architecture

- `backend/` — FastAPI + SQLAlchemy (SQLite). Runs `vvaharness estimate` / `vvaharness scan` as subprocesses using a per-run config generated from the shipped `sdk.yaml` profile (detection roles' model/backend overridden; S10/S11 disabled).
- `frontend/` — React + TypeScript + Vite dashboard. Dev server proxies `/api` to the backend.

Provider → harness backend mapping: Anthropic → `sdk`; OpenAI → `openai`; Google → `openai` via Gemini's OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai`); Custom → `openai` with the user-supplied base URL (API key optional for endpoints like local Ollama).

## Running

Requires Python ≥3.11, Node 20+, and git. The `vvaharness` CLI is installed automatically as a backend dependency (from its GitHub repo — it is not on PyPI).

Quick start — clones the repo (if needed), installs everything, and starts backend + frontend (Ctrl+C stops both):

```bash
curl -fsSL https://raw.githubusercontent.com/hicmoo/vvaharness-console/main/start.sh | bash
```

From an existing clone, just run `./start.sh`. Manual steps:

```bash
# backend
python -m venv .venv && ./.venv/bin/pip install -e backend
./.venv/bin/uvicorn backend.app.main:app --port 8000

# frontend
cd frontend && npm install && npm run dev   # http://localhost:5173
```

Runtime data (SQLite DB, encryption key, run logs, cloned targets) lives under `data/` (gitignored).

## Security notes (v1)

Single-user, local-trust deployment only: no authentication, no per-user isolation. API keys are encrypted at rest but the Fernet key lives on the same disk. Do not expose the backend to an untrusted network.
