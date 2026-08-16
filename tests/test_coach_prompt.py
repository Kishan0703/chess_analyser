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
    assert "From f3 it attacks:" in text


def test_parse_json_extracts_object_from_markdown_fence():
    text = '```json\n{"title": "Weak dark squares", "explanation": "You lost control."}\n```'

    parsed = coach._parse_json(text)

    assert parsed["title"] == "Weak dark squares"
    assert parsed["explanation"] == "You lost control."
