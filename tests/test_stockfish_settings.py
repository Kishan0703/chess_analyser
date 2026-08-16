import os
import stat
from pathlib import Path

import pytest

from backend import engine, settings


def make_executable(path):
    path.write_text("fake", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_resolve_engine_path_uses_configured_absolute_path(tmp_path):
    stockfish = tmp_path / "stockfish"
    make_executable(stockfish)

    resolved = engine.resolve_engine_path({"stockfish_path": str(stockfish)})

    assert resolved == stockfish


def test_resolve_engine_path_uses_project_relative_path(tmp_path, monkeypatch):
    stockfish = tmp_path / "engines" / "stockfish"
    stockfish.parent.mkdir()
    make_executable(stockfish)
    monkeypatch.setattr(settings, "ROOT", tmp_path)

    resolved = engine.resolve_engine_path({"stockfish_path": "engines/stockfish"})

    assert resolved == stockfish


def test_resolve_engine_path_rejects_missing_binary(tmp_path):
    missing = tmp_path / "missing-stockfish"

    with pytest.raises(FileNotFoundError) as exc:
        engine.resolve_engine_path({"stockfish_path": str(missing)})

    assert "Stockfish binary not found" in str(exc.value)


def test_resolve_engine_path_rejects_a_directory(tmp_path):
    directory = tmp_path / "stockfish"
    directory.mkdir()

    with pytest.raises(FileNotFoundError, match="not a regular file"):
        engine.resolve_engine_path({"stockfish_path": str(directory)})


@pytest.mark.skipif(os.name == "nt", reason="Windows does not use POSIX executable bits")
def test_resolve_engine_path_rejects_a_non_executable_file(tmp_path):
    stockfish = tmp_path / "stockfish"
    stockfish.write_text("fake", encoding="utf-8")
    stockfish.chmod(stat.S_IRUSR | stat.S_IWUSR)

    with pytest.raises(PermissionError, match="not executable"):
        engine.resolve_engine_path({"stockfish_path": str(stockfish)})


def test_onboarding_reports_stockfish_readiness(monkeypatch):
    from backend import app as app_module

    cfg = {
        "coach_provider": "claude",
        "stockfish_path": "engines/stockfish.exe",
        "chesscom_username": "",
        "anthropic_api_key": "key",
        "gemini_api_key": "",
    }

    class Row:
        def __getitem__(self, key):
            assert key == "c"
            return 0

    class Conn:
        def execute(self, *args):
            return self

        def fetchone(self):
            return Row()

    class ConnCtx:
        def __enter__(self):
            return Conn()

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(app_module.settings, "load", lambda: cfg)
    monkeypatch.setattr(app_module.db, "connect", lambda: ConnCtx())
    monkeypatch.setattr(app_module.engine, "resolve_engine_path", lambda _: Path("/tmp/stockfish"))

    result = app_module.onboarding()

    assert result["stockfish_path"] == "engines/stockfish.exe"
    assert result["stockfish_found"] is True
    assert result["stockfish_error"] == ""
