import json

from backend import settings


def test_save_removes_legacy_secrets_and_only_reads_environment_secrets(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"
    env_path = tmp_path / ".env"
    settings_path.write_text(json.dumps({
        "anthropic_api_key": "legacy-anthropic",
        "gemini_api_key": "legacy-gemini",
        "chesscom_username": "before",
    }), encoding="utf-8")
    env_path.write_text("ANTHROPIC_API_KEY=from-environment\n", encoding="utf-8")
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)
    monkeypatch.setattr(settings, "ENV_PATH", env_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    saved = settings.save({
        "anthropic_api_key": "submitted-anthropic",
        "gemini_api_key": "submitted-gemini",
        "chesscom_username": "after",
    })

    persisted = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "anthropic_api_key" not in persisted
    assert "gemini_api_key" not in persisted
    assert persisted["chesscom_username"] == "after"
    assert saved["anthropic_api_key"] == "from-environment"
    assert saved["gemini_api_key"] == ""


def test_default_local_coach_model_is_laptop_sized():
    assert settings.DEFAULTS["ollama_model"] == "qwen3:8b"
