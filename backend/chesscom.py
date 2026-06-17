"""Import games from the chess.com public API (free, no auth required)."""
import io
import time

import chess.pgn
import httpx

from . import db

API = "https://api.chess.com/pub"
# chess.com requires a descriptive User-Agent or it 403s
HEADERS = {"User-Agent": "ChessCoach personal analysis app (contact: levi.allen251@gmail.com)"}
RETRY_STATUSES = {429, 500, 502, 503, 504}


class ChessComImportError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _message_from_response(r: httpx.Response, username: str | None = None) -> str:
    try:
        payload = r.json()
        detail = payload.get("message") or payload.get("detail")
    except ValueError:
        detail = r.text.strip()[:180]

    if r.status_code == 404:
        who = f' "{username}"' if username else ""
        return f"Chess.com user{who} was not found. Check the username spelling."
    if r.status_code == 429:
        return "Chess.com is rate limiting imports right now. Wait a minute and try again."
    if r.status_code in {500, 502, 503, 504}:
        return "Chess.com is temporarily unavailable. Try importing again in a few minutes."
    return detail or f"Chess.com returned HTTP {r.status_code}."


def _get_json(url: str, *, timeout: int, username: str | None = None, retries: int = 2) -> dict:
    last_response = None
    for attempt in range(retries + 1):
        try:
            r = httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
        except httpx.RequestError as e:
            if attempt < retries:
                time.sleep(0.7 * (attempt + 1))
                continue
            raise ChessComImportError(f"Could not reach Chess.com: {e}", 503) from e

        if r.status_code < 400:
            return r.json()

        last_response = r
        if r.status_code in RETRY_STATUSES and attempt < retries:
            retry_after = r.headers.get("Retry-After")
            try:
                delay = min(float(retry_after), 5.0) if retry_after else 0.7 * (attempt + 1)
            except ValueError:
                delay = 0.7 * (attempt + 1)
            time.sleep(delay)
            continue
        break

    assert last_response is not None
    raise ChessComImportError(
        _message_from_response(last_response, username=username),
        503 if last_response.status_code in RETRY_STATUSES else last_response.status_code,
    )


def fetch_archives(username: str) -> list[str]:
    """Return the list of monthly archive URLs, oldest first."""
    return _get_json(
        f"{API}/player/{username}/games/archives",
        timeout=30,
        username=username,
    )["archives"]


def import_games(username: str, months: int = 3) -> dict:
    """Import the most recent `months` archives. Returns counts."""
    username = username.strip().lower()
    archives = fetch_archives(username)[-months:]
    imported = skipped = 0
    failed_archives = []
    with db.connect() as conn:
        for url in archives:
            try:
                data = _get_json(url, timeout=60, username=username)
            except ChessComImportError as e:
                if e.status_code in {429, 500, 502, 503, 504}:
                    failed_archives.append(url)
                    continue
                raise
            for g in data.get("games", []):
                pgn_text = g.get("pgn")
                if not pgn_text or g.get("rules") != "chess":  # skip variants
                    continue
                record = _parse_game(pgn_text, g, username)
                if record and db.insert_game(conn, record):
                    imported += 1
                else:
                    skipped += 1
        conn.commit()
    if failed_archives and len(failed_archives) == len(archives):
        raise ChessComImportError(
            "Chess.com is temporarily unavailable for the selected archive months. Try again in a few minutes.",
            503,
        )
    return {
        "imported": imported,
        "skipped": skipped,
        "archives": len(archives),
        "failed_archives": len(failed_archives),
    }


def _parse_game(pgn_text: str, raw: dict, username: str) -> dict | None:
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return None
    h = game.headers
    white = h.get("White", "")
    black = h.get("Black", "")
    if username == white.lower():
        user_color = "white"
    elif username == black.lower():
        user_color = "black"
    else:
        user_color = None

    def _elo(tag):
        try:
            return int(h.get(tag, ""))
        except ValueError:
            return None

    return {
        "source": "chess.com",
        "source_url": raw.get("url"),
        "pgn": pgn_text,
        "white": white,
        "black": black,
        "white_elo": _elo("WhiteElo"),
        "black_elo": _elo("BlackElo"),
        "result": h.get("Result"),
        "eco": h.get("ECO"),
        "opening": h.get("ECOUrl", "").rsplit("/", 1)[-1].replace("-", " ") or None,
        "time_control": h.get("TimeControl"),
        "played_at": f"{h.get('UTCDate', '').replace('.', '-')} {h.get('UTCTime', '')}".strip(),
        "user_color": user_color,
    }
