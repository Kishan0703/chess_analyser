"""App settings persisted to a JSON file next to the project root."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = ROOT / "settings.json"
ENV_PATH = ROOT / ".env"

ENV_KEYS = {
    "anthropic_api_key": ("ANTHROPIC_API_KEY",),
    "coach_provider": ("COACH_PROVIDER", "CHESSCOACH_PROVIDER"),
    "gemini_fallback_models": ("GEMINI_FALLBACK_MODELS",),
    "gemini_api_key": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "gemini_model": ("GEMINI_MODEL",),
}

DEFAULTS = {
    "anthropic_api_key": "",
    "gemini_api_key": "",
    "chesscom_username": "",
    "claude_model": "claude-sonnet-4-6",
    "gemini_model": "gemini-2.5-flash-lite",
    "gemini_fallback_models": "gemini-3.5-flash,gemini-3.1-flash-lite,gemini-2.5-flash",
    "engine_movetime_ms": 150,   # per-position think time for the analysis pass
    "engine_multipv": 3,
    "engine_threads": 4,
    # Coach provider: "ollama", "claude", or "gemini"
    "coach_provider": "ollama",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "qwen2.5:14b",
}


def _load_file_settings() -> dict:
    if SETTINGS_PATH.exists():
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data}
    return dict(DEFAULTS)


def _parse_env_file() -> dict:
    if not ENV_PATH.exists():
        return {}

    values = {}
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _env_overrides() -> dict:
    dotenv = _parse_env_file()
    out = {}
    for setting_key, env_names in ENV_KEYS.items():
        for env_name in env_names:
            value = os.environ.get(env_name) or dotenv.get(env_name)
            if value:
                out[setting_key] = value
                break
    return out


def load() -> dict:
    return {**_load_file_settings(), **_env_overrides()}


def save(updates: dict) -> dict:
    current = _load_file_settings()
    all_keys = set(DEFAULTS)
    for key in all_keys:
        if key in updates and updates[key] is not None:
            current[key] = updates[key]
    SETTINGS_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return {**current, **_env_overrides()}
