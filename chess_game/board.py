"""Board representation and move generation."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .pieces import Bishop, Color, King, Knight, Pawn, Piece, Queen, Rook, Square

MoveCoords = Tuple[Square, Square]


@dataclass(frozen=True)
class Move:
    """Represents a move on the chess board."""

    start: Square
    end: Square
    promotion: Optional[str] = None
    is_castling: bool = False
    is_en_passant: bool = False

    def __str__(self) -> str:  # pragma: no cover - helper
        promo = f"={self.promotion}" if self.promotion else ""
        return f"{square_to_notation(self.start)}{square_to_notation(self.end)}{promo}"


class Board:
    """The chess board with full move legality checking."""

    def __init__(self) -> None:
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.turn: Color = Color.WHITE
        self.castling_rights: Dict[Color, Dict[str, bool]] = {
            Color.WHITE: {"K": True, "Q": True},
            Color.BLACK: {"K": True, "Q": True},
        }
        self.en_passant_target: Optional[Square] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self._place_starting_pieces()

    # ------------------------------------------------------------------
    # Board setup and utilities
    # ------------------------------------------------------------------
    def _place_starting_pieces(self) -> None:
        """Place all pieces in their initial positions."""

        for col in range(8):
            self.grid[6][col] = Pawn(Color.WHITE)
            self.grid[1][col] = Pawn(Color.BLACK)

        placement = [
            (Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook),
            (Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook),
        ]
        colors = [Color.WHITE, Color.BLACK]
        rows = [7, 0]

        for color, row, pieces in zip(colors, rows, placement):
            for col, piece_cls in enumerate(pieces):
                self.grid[row][col] = piece_cls(color)

    @staticmethod
    def in_bounds(square: Square) -> bool:
        row, col = square
        return 0 <= row < 8 and 0 <= col < 8

    def get_piece(self, square: Square) -> Optional[Piece]:
        row, col = square
        if not self.in_bounds(square):
            return None
        return self.grid[row][col]

    def set_piece(self, square: Square, piece: Optional[Piece]) -> None:
        row, col = square
        self.grid[row][col] = piece

    def copy(self) -> "Board":
        return deepcopy(self)

    # ------------------------------------------------------------------
    # Move generation
    # ------------------------------------------------------------------
    def generate_legal_moves(self, color: Optional[Color] = None) -> List[Move]:
        color = color or self.turn
        pseudo_moves = list(self._generate_pseudo_legal_moves(color))
        legal_moves: List[Move] = []
        for move in pseudo_moves:
            board_copy = self.copy()
            board_copy._apply_move_no_validation(move)
            if not board_copy.is_in_check(color):
                legal_moves.append(move)
        return legal_moves

    def _generate_pseudo_legal_moves(self, color: Color) -> Iterable[Move]:
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece is None or piece.color is not color:
                    continue
                start = (row, col)
                if isinstance(piece, Pawn):
                    yield from self._pawn_moves(start, piece)
                else:
                    for end in piece.get_pseudo_legal_moves(self, start):
                        yield Move(start=start, end=end)
                if isinstance(piece, King):
                    yield from self._castling_moves(start, piece)

    def _pawn_moves(self, start: Square, pawn: Pawn) -> Iterable[Move]:
        row, col = start
        direction = pawn.color.pawn_direction

        one_forward = (row + direction, col)
        if self.in_bounds(one_forward) and self.get_piece(one_forward) is None:
            yield from self._pawn_promotions(start, one_forward, pawn)
            start_row = 6 if pawn.color is Color.WHITE else 1
            if row == start_row:
                two_forward = (row + 2 * direction, col)
                if self.get_piece(two_forward) is None:
                    yield Move(start=start, end=two_forward)

        for d_col in (-1, 1):
            capture_square = (row + direction, col + d_col)
            if not self.in_bounds(capture_square):
                continue
            target_piece = self.get_piece(capture_square)
            if target_piece is not None and target_piece.color is pawn.color.enemy:
                yield from self._pawn_promotions(start, capture_square, pawn)

        # En passant
        if self.en_passant_target is not None:
            if (row + direction, col - 1) == self.en_passant_target or (
                row + direction,
                col + 1,
            ) == self.en_passant_target:
                target_col = self.en_passant_target[1]
                capture_square = (row + direction, target_col)
                yield Move(start=start, end=capture_square, is_en_passant=True)

    def _pawn_promotions(self, start: Square, end: Square, pawn: Pawn) -> Iterable[Move]:
        last_rank = 0 if pawn.color is Color.WHITE else 7
        if end[0] == last_rank:
            for symbol in ("q", "r", "b", "n"):
                yield Move(start=start, end=end, promotion=symbol)
        else:
            yield Move(start=start, end=end)

    def _castling_moves(self, start: Square, king: King) -> Iterable[Move]:
        rights = self.castling_rights[king.color]
        row, col = start
        if self.is_in_check(king.color):
            return

        if rights["K"]:
            squares_between = [(row, col + 1), (row, col + 2)]
            if all(self.get_piece(sq) is None for sq in squares_between):
                if not any(self.is_square_attacked(sq, king.color.enemy) for sq in squares_between):
                    rook_square = (row, 7)
                    rook = self.get_piece(rook_square)
                    if isinstance(rook, Rook) and rook.color is king.color:
                        yield Move(start=start, end=(row, col + 2), is_castling=True)

        if rights["Q"]:
            squares_between = [(row, col - 1), (row, col - 2), (row, col - 3)]
            if all(self.get_piece(sq) is None for sq in squares_between[:-1]):
                if not any(self.is_square_attacked(sq, king.color.enemy) for sq in squares_between[:-1]):
                    rook_square = (row, 0)
                    rook = self.get_piece(rook_square)
                    if isinstance(rook, Rook) and rook.color is king.color and self.get_piece(squares_between[-1]) is None:
                        yield Move(start=start, end=(row, col - 2), is_castling=True)

    # ------------------------------------------------------------------
    # Move application and state tracking
    # ------------------------------------------------------------------
    def apply_move(self, move: Move) -> None:
        if move not in self.generate_legal_moves(self.turn):
            raise ValueError("Illegal move")
        self._apply_move_no_validation(move)
        self._post_move_updates(move)

    def _apply_move_no_validation(self, move: Move) -> None:
        piece = self.get_piece(move.start)
        if piece is None:
            raise ValueError("No piece at start square")

        target_piece = self.get_piece(move.end)
        captured_piece = target_piece
        captured = target_piece is not None
        if move.is_en_passant:
            capture_row = move.start[0]
            capture_col = move.end[1]
            captured_piece = self.get_piece((capture_row, capture_col))
            captured = captured_piece is not None
            self.set_piece((capture_row, capture_col), None)

        self.set_piece(move.start, None)
        if move.promotion:
            promoted_piece = self._create_promotion_piece(piece.color, move.promotion)
            self.set_piece(move.end, promoted_piece)
        else:
            self.set_piece(move.end, piece)

        if isinstance(piece, King) and move.is_castling:
            self._move_castling_rook(move)

        self._update_castling_rights(move, piece, captured_piece=captured_piece)
        self._update_en_passant(move, piece)
        self._update_halfmove_clock(piece, captured)

    def _move_castling_rook(self, move: Move) -> None:
        row = move.start[0]
        if move.end[1] == 6:  # king side
            rook_start = (row, 7)
            rook_end = (row, 5)
        else:  # queen side
            rook_start = (row, 0)
            rook_end = (row, 3)
        rook = self.get_piece(rook_start)
        self.set_piece(rook_start, None)
        self.set_piece(rook_end, rook)

    def _create_promotion_piece(self, color: Color, symbol: str) -> Piece:
        mapping = {
            "q": Queen,
            "r": Rook,
            "b": Bishop,
            "n": Knight,
        }
        if symbol.lower() not in mapping:
            raise ValueError("Invalid promotion piece")
        return mapping[symbol.lower()](color)

    def _update_castling_rights(
        self,
        move: Move,
        piece: Piece,
        captured_piece: Optional[Piece],
    ) -> None:
        if isinstance(piece, King):
            self.castling_rights[piece.color]["K"] = False
            self.castling_rights[piece.color]["Q"] = False
        if isinstance(piece, Rook):
            if move.start[1] == 0:
                self.castling_rights[piece.color]["Q"] = False
            elif move.start[1] == 7:
                self.castling_rights[piece.color]["K"] = False
        if isinstance(captured_piece, Rook):
            if move.end == (7, 0):
                self.castling_rights[Color.WHITE]["Q"] = False
            elif move.end == (7, 7):
                self.castling_rights[Color.WHITE]["K"] = False
            elif move.end == (0, 0):
                self.castling_rights[Color.BLACK]["Q"] = False
            elif move.end == (0, 7):
                self.castling_rights[Color.BLACK]["K"] = False

    def _update_en_passant(self, move: Move, piece: Piece) -> None:
        if isinstance(piece, Pawn) and abs(move.start[0] - move.end[0]) == 2:
            row = (move.start[0] + move.end[0]) // 2
            self.en_passant_target = (row, move.start[1])
        else:
            self.en_passant_target = None

    def _update_halfmove_clock(self, piece: Piece, captured: bool) -> None:
        if isinstance(piece, Pawn) or captured:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

    def _post_move_updates(self, move: Move) -> None:
        self.turn = self.turn.enemy
        if self.turn is Color.WHITE:
            self.fullmove_number += 1

    # ------------------------------------------------------------------
    # Game state queries
    # ------------------------------------------------------------------
    def is_in_check(self, color: Color) -> bool:
        king_square = self._find_king(color)
        if king_square is None:
            return False
        return self.is_square_attacked(king_square, color.enemy)

    def _find_king(self, color: Color) -> Optional[Square]:
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if isinstance(piece, King) and piece.color is color:
                    return (row, col)
        return None

    def is_square_attacked(self, square: Square, by_color: Color) -> bool:
        row, col = square

        # Pawns
        direction = -1 if by_color is Color.WHITE else 1
        for d_col in (-1, 1):
            attacker = self.get_piece((row + direction, col + d_col))
            if isinstance(attacker, Pawn) and attacker.color is by_color:
                return True

        # Knights
        for d_row, d_col in (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ):
            attacker = self.get_piece((row + d_row, col + d_col))
            if isinstance(attacker, Knight) and attacker.color is by_color:
                return True

        # Sliding pieces
        sliding_directions = {
            Queen: [
                (1, 0),
                (-1, 0),
                (0, 1),
                (0, -1),
                (1, 1),
                (1, -1),
                (-1, 1),
                (-1, -1),
            ],
            Rook: [(1, 0), (-1, 0), (0, 1), (0, -1)],
            Bishop: [(1, 1), (1, -1), (-1, 1), (-1, -1)],
        }
        for piece_type, directions in sliding_directions.items():
            for d_row, d_col in directions:
                r, c = row + d_row, col + d_col
                while self.in_bounds((r, c)):
                    occupant = self.get_piece((r, c))
                    if occupant is None:
                        r += d_row
                        c += d_col
                        continue
                    if isinstance(occupant, piece_type) and occupant.color is by_color:
                        return True
                    break

        # Kings
        for d_row in (-1, 0, 1):
            for d_col in (-1, 0, 1):
                if d_row == 0 and d_col == 0:
                    continue
                attacker = self.get_piece((row + d_row, col + d_col))
                if isinstance(attacker, King) and attacker.color is by_color:
                    return True

        return False

    def has_legal_moves(self, color: Color) -> bool:
        return bool(self.generate_legal_moves(color))

    def result(self) -> Optional[str]:
        if self.is_in_check(self.turn):
            if not self.has_legal_moves(self.turn):
                return f"{self.turn.enemy.value} wins by checkmate"
        else:
            if not self.has_legal_moves(self.turn):
                return "Draw by stalemate"
        if self.halfmove_clock >= 100:
            return "Draw by fifty-move rule"
        return None

    # ------------------------------------------------------------------
    # Display utilities
    # ------------------------------------------------------------------
    def __str__(self) -> str:  # pragma: no cover - formatting helper
        rows = []
        for row in range(8):
            cells = []
            for col in range(8):
                piece = self.grid[row][col]
                cells.append(str(piece) if piece else ".")
            rows.append(f"{8 - row} {' '.join(cells)}")
        rows.append("  a b c d e f g h")
        return "\n".join(rows)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def square_to_notation(square: Square) -> str:
    return f"{chr(ord('a') + square[1])}{8 - square[0]}"


def notation_to_square(text: str) -> Square:
    col = ord(text[0].lower()) - ord("a")
    row = 8 - int(text[1])
    return (row, col)
