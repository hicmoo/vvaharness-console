"""Provider API clients: key verification and model listing.

Providers are consumed through HTTP APIs:
- anthropic: native Anthropic API (/v1/models)
- openai:    OpenAI-compatible /v1/models
- google:    Gemini's OpenAI-compatible endpoint
- custom:    any OpenAI-compatible endpoint (Ollama, Groq, OpenRouter, HF, ...)
"""

import httpx

GOOGLE_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
OPENAI_BASE_URL = "https://api.openai.com/v1"
ANTHROPIC_BASE_URL = "https://api.anthropic.com"


class ProviderError(Exception):
    pass


def default_base_url(kind: str) -> str:
    if kind == "anthropic":
        return ANTHROPIC_BASE_URL
    if kind == "openai":
        return OPENAI_BASE_URL
    if kind == "google":
        return GOOGLE_OPENAI_BASE_URL
    if kind == "custom":
        raise ProviderError("custom providers require a base URL")
    raise ProviderError(f"unknown provider kind: {kind}")


def list_models(
    kind: str, api_key: str, base_url: str | None = None
) -> list[dict[str, str | None]]:
    base = (base_url or default_base_url(kind)).rstrip("/")
    try:
        if kind == "anthropic":
            resp = httpx.get(
                f"{base}/v1/models",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                params={"limit": 100},
                timeout=20,
            )
            resp.raise_for_status()
            return [
                {"id": m["id"], "display_name": m.get("display_name")}
                for m in resp.json().get("data", [])
            ]
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        resp = httpx.get(f"{base}/models", headers=headers, timeout=20)
        resp.raise_for_status()
        models = []
        for m in resp.json().get("data", []):
            model_id = m.get("id", "")
            if kind == "google":
                model_id = model_id.removeprefix("models/")
            models.append({"id": model_id, "display_name": None})
        return sorted(models, key=lambda m: m["id"] or "")
    except httpx.HTTPStatusError as e:
        raise ProviderError(f"{kind} API returned {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise ProviderError(f"could not reach {kind} API: {e.__class__.__name__}") from e


def verify_key(kind: str, api_key: str, base_url: str | None = None) -> bool:
    try:
        list_models(kind, api_key, base_url)
        return True
    except ProviderError:
        return False
