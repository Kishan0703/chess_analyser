from pathlib import Path

import pytest

from backend import engine, settings


def test_resolve_engine_path_uses_configured_absolute_path(tmp_path):
    stockfish = tmp_path / "stockfish"
    stockfish.write_text("fake", encoding="utf-8")

    resolved = engine.resolve_engine_path({"stockfish_path": str(stockfish)})

    assert resolved == stockfish


def test_resolve_engine_path_uses_project_relative_path(tmp_path, monkeypatch):
    stockfish = tmp_path / "engines" / "stockfish"
    stockfish.parent.mkdir()
    stockfish.write_text("fake", encoding="utf-8")
    monkeypatch.setattr(settings, "ROOT", tmp_path)

    resolved = engine.resolve_engine_path({"stockfish_path": "engines/stockfish"})

    assert resolved == stockfish


def test_resolve_engine_path_rejects_missing_binary(tmp_path):
    missing = tmp_path / "missing-stockfish"

    with pytest.raises(FileNotFoundError) as exc:
        engine.resolve_engine_path({"stockfish_path": str(missing)})

    assert "Stockfish binary not found" in str(exc.value)
