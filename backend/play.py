"""Authoritative domain logic for local human-versus-Stockfish games."""
import io
import random
from collections.abc import Callable

import chess
import chess.engine
import chess.pgn

from . import db, engine, settings


DIFFICULTY_PRESETS = {
    "beginner": {"label": "Beginner", "skill_level": 2, "move_time_ms": 80, "randomness": 0.55},
    "casual": {"label": "Casual", "skill_level": 5, "move_time_ms": 150, "randomness": 0.35},
    "club": {"label": "Club", "skill_level": 8, "move_time_ms": 250, "randomness": 0.20},
    "strong": {"label": "Strong", "skill_level": 13, "move_time_ms": 500, "randomness": 0.08},
    "master": {"label": "Master", "skill_level": 18, "move_time_ms": 900, "randomness": 0.0},
}


def _legal_moves(board: chess.Board) -> list[dict]:
    return [
        {"uci": move.uci(), "from": chess.square_name(move.from_square),
         "to": chess.square_name(move.to_square),
         "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
         "san": board.san(move)}
        for move in board.legal_moves
    ]


def _status_for(board: chess.Board) -> tuple[str, str]:
    if board.is_checkmate():
        return "finished", "1-0" if board.turn == chess.BLACK else "0-1"
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return "finished", "1/2-1/2"
    return "active", "*"


def _pick_ranked_move(moves: list[chess.Move], randomness: float) -> chess.Move:
    if not moves:
        raise ValueError("Stockfish returned no legal moves")
    if randomness <= 0 or len(moves) == 1 or random.random() >= randomness:
        return moves[0]
    return moves[1 + int(random.random() * (len(moves) - 1))]


def choose_bot_move(board: chess.Board, advanced: dict) -> chess.Move:
    cfg = settings.load()
    sf = chess.engine.SimpleEngine.popen_uci(str(engine.resolve_engine_path(cfg)))
    try:
        try:
            sf.configure({"Skill Level": int(advanced["skill_level"])})
        except Exception:
            pass
        multipv = 1 if float(advanced["randomness"]) <= 0 else 3
        infos = sf.analyse(
            board,
            chess.engine.Limit(time=int(advanced["move_time_ms"]) / 1000),
            multipv=multipv,
        )
        if isinstance(infos, dict):
            infos = [infos]
        moves = [info["pv"][0] for info in infos if info.get("pv")]
        return _pick_ranked_move(moves, float(advanced["randomness"]))
    finally:
        sf.quit()


def _move_from_payload(move: dict) -> chess.Move:
    try:
        uci = f"{move['from']}{move['to']}{move.get('promotion') or ''}"
        return chess.Move.from_uci(uci)
    except (KeyError, ValueError) as e:
        raise ValueError("illegal move") from e


def _move_data(board: chess.Board, move: chess.Move) -> dict:
    return {
        "uci": move.uci(),
        "from": chess.square_name(move.from_square),
        "to": chess.square_name(move.to_square),
        "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
        "san": board.san(move),
    }


def _append_pgn(pgn: str, moves: list[chess.Move], result: str) -> str:
    game = chess.pgn.read_game(io.StringIO(pgn)) if pgn else chess.pgn.Game()
    if game is None:
        raise ValueError("stored bot game has invalid PGN")
    node = game.end()
    for move in moves:
        node = node.add_variation(move)
    game.headers["Result"] = result
    return game.accept(chess.pgn.StringExporter(headers=False, variations=False, comments=False))


def _board_from_session(session: dict) -> chess.Board:
    if not session["pgn"]:
        return chess.Board(session["fen"])
    game = chess.pgn.read_game(io.StringIO(session["pgn"]))
    if game is None:
        raise ValueError("stored bot game has invalid PGN")
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    return board


def serialize_board_state(session: dict, board: chess.Board) -> dict:
    return {
        "id": session["id"],
        "player_color": session["player_color"],
        "difficulty": session["difficulty"],
        "advanced": session["advanced"],
        "pgn": session["pgn"],
        "fen": board.fen(),
        "status": session["status"],
        "result": session["result"],
        "legal_moves": _legal_moves(board) if session["status"] == "active" else [],
    }


def new_game(player_color: str, difficulty: str, advanced: dict | None = None,
             bot_selector: Callable[[chess.Board, dict], chess.Move] | None = None) -> dict:
    if player_color not in {"white", "black"}:
        raise ValueError("player_color must be 'white' or 'black'")
    if difficulty not in DIFFICULTY_PRESETS:
        raise ValueError("unknown difficulty")

    config = dict(DIFFICULTY_PRESETS[difficulty])
    if advanced is not None:
        config.update(advanced)
    board = chess.Board()
    session = {
        "player_color": player_color,
        "difficulty": difficulty,
        "advanced": config,
        "pgn": "",
        "fen": board.fen(),
        "status": "active",
        "result": "*",
    }
    last_bot_move = None
    if player_color == "black":
        selector = bot_selector or choose_bot_move
        bot_move = selector(board, config)
        if bot_move not in board.legal_moves:
            raise ValueError("bot selector returned an illegal move")
        last_bot_move = _move_data(board, bot_move)
        board.push(bot_move)
        session.update({
            "pgn": _append_pgn("", [bot_move], "*"),
            "fen": board.fen(),
        })
    with db.connect() as conn:
        session["id"] = db.create_bot_game(conn, session)
    state = serialize_board_state(session, board)
    if last_bot_move is not None:
        state["last_bot_move"] = last_bot_move
    return state


def get_game(bot_game_id: int) -> dict:
    with db.connect() as conn:
        session = db.get_bot_game(conn, bot_game_id)
    if session is None:
        raise ValueError(f"bot game {bot_game_id} not found")
    return serialize_board_state(session, _board_from_session(session))


def save_to_game(bot_game_id: int) -> dict:
    with db.connect() as conn:
        session = db.get_bot_game(conn, bot_game_id)
        if session is None:
            raise ValueError("bot game not found")
        if session.get("saved_game_id"):
            return {"game_id": session["saved_game_id"]}
        if session["status"] != "finished":
            raise ValueError("bot game is not finished")

        game_id = db.insert_game(conn, {
            "source": "local-bot",
            "source_url": f"local-bot:{bot_game_id}",
            "pgn": session["pgn"],
            "white": "You" if session["player_color"] == "white" else "ChessCoach Bot",
            "black": "ChessCoach Bot" if session["player_color"] == "white" else "You",
            "white_elo": None,
            "black_elo": None,
            "result": session["result"],
            "eco": None,
            "opening": "Bot practice",
            "time_control": "offline",
            "played_at": None,
            "user_color": session["player_color"],
        })
        if game_id is None:
            row = conn.execute(
                "SELECT id FROM games WHERE source_url = ?", (f"local-bot:{bot_game_id}",)
            ).fetchone()
            game_id = row["id"]
        db.mark_bot_game_saved(conn, bot_game_id, game_id)
        conn.commit()
        return {"game_id": game_id}


def apply_player_move(bot_game_id: int, move: dict,
                      bot_selector: Callable[[chess.Board, dict], chess.Move] | None = None) -> dict:
    with db.connect() as conn:
        session = db.get_bot_game(conn, bot_game_id)
        if session is None:
            raise ValueError(f"bot game {bot_game_id} not found")
        if session["status"] != "active":
            raise ValueError("bot game is finished")

        board = _board_from_session(session)
        player_color = chess.WHITE if session["player_color"] == "white" else chess.BLACK
        if board.turn != player_color:
            raise ValueError("not the player's turn")

        player_move = _move_from_payload(move)
        if player_move not in board.legal_moves:
            raise ValueError("illegal move")
        last_player_move = _move_data(board, player_move)
        board.push(player_move)
        moves = [player_move]
        last_bot_move = None

        status, result = _status_for(board)
        if status == "active":
            selector = bot_selector or choose_bot_move
            bot_move = selector(board, session["advanced"])
            if bot_move not in board.legal_moves:
                raise ValueError("bot selector returned an illegal move")
            last_bot_move = _move_data(board, bot_move)
            board.push(bot_move)
            moves.append(bot_move)
            status, result = _status_for(board)

        session.update({
            "pgn": _append_pgn(session["pgn"], moves, result),
            "fen": board.fen(),
            "status": status,
            "result": result,
        })
        db.update_bot_game(conn, bot_game_id, session)

    state = serialize_board_state(session, board)
    state["last_player_move"] = last_player_move
    state["last_bot_move"] = last_bot_move
    return state
