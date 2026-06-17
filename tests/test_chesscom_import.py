import pytest

from backend import chesscom


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = {}

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_get_json_user_not_found(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse(404, {"message": 'User "missing" not found.'})

    monkeypatch.setattr(chesscom.httpx, "get", fake_get)

    with pytest.raises(chesscom.ChessComImportError) as exc:
        chesscom._get_json("https://example.test", timeout=1, username="missing", retries=0)

    assert exc.value.status_code == 404
    assert "not found" in str(exc.value)


def test_import_skips_transient_archive_failure(monkeypatch):
    archives = ["https://archive.test/ok", "https://archive.test/down"]

    def fake_fetch_archives(username):
        return archives

    def fake_get_json(url, **kwargs):
        if url == "https://archive.test/down":
            raise chesscom.ChessComImportError("temporary", 503)
        return {"games": []}

    class FakeConn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def commit(self):
            pass

    monkeypatch.setattr(chesscom, "fetch_archives", fake_fetch_archives)
    monkeypatch.setattr(chesscom, "_get_json", fake_get_json)
    monkeypatch.setattr(chesscom.db, "connect", lambda: FakeConn())

    result = chesscom.import_games("player", months=2)

    assert result["archives"] == 2
    assert result["failed_archives"] == 1
