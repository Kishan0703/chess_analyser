"""SQLite aggregation helpers for a player's chess profile."""
import sqlite3


def get_profile(conn: sqlite3.Connection, username: str | None = None,
                limit_games: int = 200) -> dict:
    name = username.strip().lower() if username else None
    user_where = ""
    user_params: list = []
    if name:
        user_where = "WHERE lower(g.white) = ? OR lower(g.black) = ? OR g.source = 'local-bot'"
        user_params = [name, name]

    games = [dict(r) for r in conn.execute(
        f"""SELECT g.*,
                  EXISTS(SELECT 1 FROM analyses a WHERE a.game_id = g.id) AS coached
           FROM games g
           {user_where}
           ORDER BY g.played_at DESC
           LIMIT ?""",
        [*user_params, limit_games],
    ).fetchall()]

    game_ids = [g["id"] for g in games]
    if not game_ids:
        return {
            "summary": {
                "games": 0, "analyzed": 0, "coached": 0, "wins": 0, "losses": 0,
                "draws": 0, "unknown_results": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0,
                "avg_win_pct_loss": 0.0,
            },
            "move_quality": [],
            "themes": [],
            "openings": [],
            "recent": [],
        }

    analyzed_games = [g for g in games if g.get("engine_analyzed")]
    analyzed_game_ids = [g["id"] for g in analyzed_games]

    def user_color_for(g: dict) -> str | None:
        if g.get("source") == "local-bot":
            return g.get("user_color")
        if name == (g.get("white") or "").lower():
            return "white"
        if name == (g.get("black") or "").lower():
            return "black"
        return g.get("user_color")

    def is_user_move(ply: int, color: str | None) -> bool:
        if color is None:
            return True
        return (color == "white") == (ply % 2 == 1)

    def result_for(g: dict) -> str:
        result = g.get("result")
        color = user_color_for(g)
        if result == "1/2-1/2":
            return "draw"
        if result == "1-0" and color == "white":
            return "win"
        if result == "1-0" and color == "black":
            return "loss"
        if result == "0-1" and color == "black":
            return "win"
        if result == "0-1" and color == "white":
            return "loss"
        return "unknown"

    moves_by_game: dict[int, list[dict]] = {gid: [] for gid in analyzed_game_ids}
    if analyzed_game_ids:
        placeholders = ",".join("?" for _ in analyzed_game_ids)
        for r in conn.execute(
            f"""SELECT game_id, ply, classification, win_pct_loss
                FROM moves
                WHERE game_id IN ({placeholders})""",
            analyzed_game_ids,
        ):
            moves_by_game[r["game_id"]].append(dict(r))

    classifications = {"blunder": 0, "mistake": 0, "inaccuracy": 0, "best": 0, "great": 0,
                       "brilliant": 0, "good": 0}
    losses = []
    for g in analyzed_games:
        color = user_color_for(g)
        for m in moves_by_game[g["id"]]:
            if not is_user_move(m["ply"], color):
                continue
            cls = m.get("classification")
            if cls in classifications:
                classifications[cls] += 1
            if cls in {"blunder", "mistake", "inaccuracy"} and m.get("win_pct_loss") is not None:
                losses.append(float(m["win_pct_loss"]))

    theme_rows = []
    if analyzed_game_ids:
        theme_rows = [dict(r) for r in conn.execute(
            f"""SELECT slug,
                      COUNT(*) AS count,
                      SUM(CASE WHEN severity = 'decisive' THEN 1 ELSE 0 END) AS decisive,
                      SUM(CASE WHEN severity = 'significant' THEN 1 ELSE 0 END) AS significant,
                      SUM(CASE WHEN severity = 'minor' THEN 1 ELSE 0 END) AS minor
                FROM themes
                WHERE game_id IN ({placeholders})
                  AND (side IS NULL OR side IN ('user', 'both'))
                GROUP BY slug
                ORDER BY count DESC, slug ASC
                LIMIT 12""",
            analyzed_game_ids,
        ).fetchall()]

    openings = []
    for opening in sorted({g.get("opening") or g.get("eco") or "Unknown" for g in analyzed_games}):
        group = [g for g in analyzed_games if (g.get("opening") or g.get("eco") or "Unknown") == opening]
        opening_losses = []
        for g in group:
            color = user_color_for(g)
            for m in moves_by_game[g["id"]]:
                if (is_user_move(m["ply"], color)
                        and m.get("classification") in {"blunder", "mistake", "inaccuracy"}
                        and m.get("win_pct_loss") is not None):
                    opening_losses.append(float(m["win_pct_loss"]))
        openings.append({
            "opening": opening,
            "games": len(group),
            "wins": sum(1 for g in group if result_for(g) == "win"),
            "losses": sum(1 for g in group if result_for(g) == "loss"),
            "draws": sum(1 for g in group if result_for(g) == "draw"),
            "avg_loss": round(sum(opening_losses) / len(opening_losses), 1) if opening_losses else 0.0,
        })
    openings.sort(key=lambda o: (o["losses"], o["avg_loss"], o["games"]), reverse=True)

    themes_by_game: dict[int, list[str]] = {gid: [] for gid in analyzed_game_ids}
    if analyzed_game_ids:
        for r in conn.execute(
            f"""SELECT game_id, slug FROM themes
                WHERE game_id IN ({placeholders})
                  AND (side IS NULL OR side IN ('user', 'both'))
                ORDER BY slug""",
            analyzed_game_ids,
        ):
            themes_by_game[r["game_id"]].append(r["slug"])

    recent = []
    for g in analyzed_games[:10]:
        color = user_color_for(g)
        user_moves = [m for m in moves_by_game[g["id"]] if is_user_move(m["ply"], color)]
        opponent = g.get("black") if color == "white" else g.get("white")
        recent.append({
            "game_id": g["id"],
            "played_at": g.get("played_at"),
            "opponent": opponent or "",
            "result": result_for(g),
            "blunders": sum(1 for m in user_moves if m.get("classification") == "blunder"),
            "mistakes": sum(1 for m in user_moves if m.get("classification") == "mistake"),
            "themes": themes_by_game[g["id"]][:4],
        })

    return {
        "summary": {
            "games": len(games),
            "analyzed": sum(1 for g in games if g.get("engine_analyzed")),
            "coached": sum(1 for g in games if g.get("coached")),
            "wins": sum(1 for g in games if result_for(g) == "win"),
            "losses": sum(1 for g in games if result_for(g) == "loss"),
            "draws": sum(1 for g in games if result_for(g) == "draw"),
            "unknown_results": sum(1 for g in games if result_for(g) == "unknown"),
            "blunders": classifications["blunder"],
            "mistakes": classifications["mistake"],
            "inaccuracies": classifications["inaccuracy"],
            "avg_win_pct_loss": round(sum(losses) / len(losses), 1) if losses else 0.0,
        },
        "move_quality": [
            {"classification": cls, "count": count}
            for cls, count in classifications.items()
            if count
        ],
        "themes": theme_rows,
        "openings": openings[:8],
        "recent": recent,
    }
