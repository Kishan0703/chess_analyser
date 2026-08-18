import chess

from backend import coach, features


def test_piece_placement_lists_exact_squares():
    board = chess.Board()
    placement = features.piece_placement(board)

    assert "White: Ke1, Qd1" in placement
    assert "Black: Ke8, Qd8" in placement


def test_move_consequences_does_not_invent_attacks():
    board = chess.Board()
    text = features.move_consequences(board, chess.Move.from_uci("g1f3"))

    assert "The moved knight lands on f3" in text
    assert "- From f3 it attacks: NO enemy pieces" in text


def test_move_consequences_lists_a_known_attacked_enemy_piece():
    board = chess.Board("4k3/8/8/4p3/8/8/8/4K1N1 w - - 0 1")
    text = features.move_consequences(board, chess.Move.from_uci("g1f3"))

    assert "- From f3 it attacks: pawn on e5" in text


def test_moment_block_contains_piece_placement_and_move_consequences():
    moment = {
        "ply": 1,
        "san": "Nf3",
        "uci": "g1f3",
        "best_san": "e4",
        "best_line": "e4 e5",
        "eval_cp": 0,
        "eval_mate": None,
        "win_pct_loss": 12.0,
    }

    block = coach._moment_block(moment, chess.STARTING_FEN, "white")

    assert "PIECE PLACEMENT before your move" in block
    assert "White: Ke1, Qd1" in block
    assert "CONSEQUENCES of Nf3" in block
    assert "- From f3 it attacks: NO enemy pieces" in block


def test_parse_json_extracts_object_from_markdown_fence():
    text = '```json\n{"title": "Weak dark squares", "explanation": "You lost control."}\n```'

    parsed = coach._parse_json(text)

    assert parsed["title"] == "Weak dark squares"
    assert parsed["explanation"] == "You lost control."


def test_call_ollama_records_timing_metrics(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "message": {"content": '{"title":"Fast","explanation":"Grounded."}'},
                "prompt_eval_count": 123,
                "prompt_eval_duration": 456_000_000,
                "eval_count": 17,
                "eval_duration": 89_000_000,
            }

    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(coach.httpx, "post", fake_post)
    metrics = {}

    text, model, input_tokens, output_tokens = coach._call_ollama(
        "Explain the moment.",
        {"ollama_url": "http://ollama.local/", "ollama_model": "qwen3:8b"},
        "System",
        metrics=metrics,
    )

    assert text == '{"title":"Fast","explanation":"Grounded."}'
    assert model == "qwen3:8b"
    assert input_tokens == 123
    assert output_tokens == 17
    assert metrics == {
        "ollama_calls": 1,
        "ollama_prompt_eval_count": 123,
        "ollama_eval_count": 17,
        "ollama_prompt_eval_duration": 456_000_000,
        "ollama_eval_duration": 89_000_000,
    }
    assert captured["url"] == "http://ollama.local/api/chat"
    assert captured["payload"]["options"]["think"] is False
