"""Generate a per-run vvaharness config.

Per the vvaharness operating manual, config files are never hand-written:
the sanctioned customization path is copying a shipped profile and editing
the copy. We copy the shipped ``sdk.yaml`` profile and override only the
model roles (id + backend) for the provider the user selected, and disable
S10/S11 so a scan never edits target source.
"""

from pathlib import Path

import vvaharness
import yaml

DETECTION_ROLES = (
    "autoexclude",
    "preprocess",
    "threatmodel",
    "decompose",
    "deepdive",
    "verify",
    "dedup",
    "chain",
)

# vvaharness backend used per provider kind. Google is consumed through
# Gemini's OpenAI-compatible endpoint, so it rides the `openai` backend.
PROVIDER_BACKEND = {"anthropic": "sdk", "openai": "openai", "google": "openai"}


def shipped_profile_path(name: str = "sdk.yaml") -> Path:
    return Path(vvaharness.__file__).resolve().parent / "config" / "profiles" / name


def generate_config(run_dir: Path, provider_kind: str, model_id: str) -> Path:
    base = yaml.safe_load(shipped_profile_path().read_text())
    via = PROVIDER_BACKEND[provider_kind]

    models = base.setdefault("models", {})
    for role in DETECTION_ROLES:
        existing = models.get(role)
        role_cfg = dict(existing) if isinstance(existing, dict) else {}
        role_cfg["id"] = model_id
        role_cfg["via"] = via
        models[role] = role_cfg

    # Detection-only: never remediate (edits target source) or validate.
    base.setdefault("step_remediate", {})["enabled"] = False
    base.setdefault("step_validate", {})["enabled"] = False

    config_path = run_dir / "config.yaml"
    config_path.write_text(yaml.safe_dump(base, sort_keys=False))
    return config_path
