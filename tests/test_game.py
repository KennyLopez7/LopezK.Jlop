"""Integration tests for the chess game."""
from chess_game import Game
from chess_game.board import notation_to_square
from chess_game.pieces import Color, King, Pawn, Queen


def test_initial_moves():
    game = Game()
    moves = list(game.legal_moves())
    assert len(moves) == 20
    assert any(
        move.start == notation_to_square("e2") and move.end == notation_to_square("e4")
        for move in moves
    )
    assert any(
        move.start == notation_to_square("g1") and move.end == notation_to_square("f3")
        for move in moves
    )


def play_moves(game: Game, *moves: str) -> None:
    for move in moves:
        game.move_from_string(move)


def test_fools_mate_checkmate():
    game = Game()
    play_moves(game, "f2f3", "e7e5", "g2g4", "d8h4")
    assert game.board.result() == "black wins by checkmate"


def test_castling_white_king_side():
    game = Game()
    play_moves(game, "g1f3", "g8f6", "e2e4", "e7e5", "f1e2", "f8e7")
    result = game.move_from_string("O-O")
    assert game.board.get_piece(notation_to_square("g1")).name == "king"
    assert game.board.get_piece(notation_to_square("f1")).name == "rook"
    assert result.note is None


def test_en_passant_capture():
    game = Game()
    play_moves(game, "e2e4", "a7a6", "e4e5", "d7d5")
    game.move_from_string("e5d6")
    assert game.board.get_piece(notation_to_square("d6")).name == "pawn"
    assert game.board.get_piece(notation_to_square("d5")) is None


def test_promotion_to_queen():
    game = Game()
    board = game.board
    board.grid = [[None for _ in range(8)] for _ in range(8)]
    board.turn = Color.WHITE
    board.castling_rights = {
        Color.WHITE: {"K": False, "Q": False},
        Color.BLACK: {"K": False, "Q": False},
    }
    board.en_passant_target = None
    board.halfmove_clock = 0
    board.fullmove_number = 1
    board.set_piece(notation_to_square("h1"), King(Color.WHITE))
    board.set_piece(notation_to_square("h8"), King(Color.BLACK))
    board.set_piece(notation_to_square("a7"), Pawn(Color.WHITE))
    game.move_from_string("a7a8q")
    piece = game.board.get_piece(notation_to_square("a8"))
    assert isinstance(piece, Queen)
