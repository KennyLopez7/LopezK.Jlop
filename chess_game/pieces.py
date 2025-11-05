"""Piece definitions for the chess game."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Tuple, TYPE_CHECKING

Square = Tuple[int, int]


class Color(Enum):
    """Enumeration for the two sides in chess."""

    WHITE = "white"
    BLACK = "black"

    @property
    def pawn_direction(self) -> int:
        """Return the row increment a pawn of this color moves."""

        return -1 if self is Color.WHITE else 1

    @property
    def enemy(self) -> "Color":
        return Color.BLACK if self is Color.WHITE else Color.WHITE


@dataclass(frozen=True)
class Piece:
    """Base class for all chess pieces."""

    color: Color
    name: str
    symbol: str

    def get_pseudo_legal_moves(self, board: "Board", square: Square) -> Iterable[Square]:
        raise NotImplementedError

    def __str__(self) -> str:  # pragma: no cover - trivial
        display = self.symbol.upper() if self.color is Color.WHITE else self.symbol.lower()
        return display


class SlidingPiece(Piece):
    """Common behaviour for bishops, rooks and queens."""

    directions: Tuple[Tuple[int, int], ...]

    def get_pseudo_legal_moves(self, board: "Board", square: Square) -> Iterable[Square]:
        moves: List[Square] = []
        for d_row, d_col in self.directions:
            row, col = square
            while True:
                row += d_row
                col += d_col
                if not board.in_bounds((row, col)):
                    break
                target_piece = board.get_piece((row, col))
                if target_piece is None:
                    moves.append((row, col))
                    continue
                if target_piece.color is not self.color:
                    moves.append((row, col))
                break
        return moves


class Bishop(SlidingPiece):
    def __init__(self, color: Color):
        super().__init__(color=color, name="bishop", symbol="b")
        self.directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))


class Rook(SlidingPiece):
    def __init__(self, color: Color):
        super().__init__(color=color, name="rook", symbol="r")
        self.directions = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Queen(SlidingPiece):
    def __init__(self, color: Color):
        super().__init__(color=color, name="queen", symbol="q")
        self.directions = (
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        )


class Knight(Piece):
    """Knight moves in L-shapes."""

    _OFFSETS: Tuple[Square, ...] = (
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    )

    def __init__(self, color: Color):
        super().__init__(color=color, name="knight", symbol="n")

    def get_pseudo_legal_moves(self, board: "Board", square: Square) -> Iterable[Square]:
        moves: List[Square] = []
        row, col = square
        for d_row, d_col in self._OFFSETS:
            target = (row + d_row, col + d_col)
            if not board.in_bounds(target):
                continue
            target_piece = board.get_piece(target)
            if target_piece is None or target_piece.color is not self.color:
                moves.append(target)
        return moves


class King(Piece):
    """King moves one square in any direction."""

    _OFFSETS: Tuple[Square, ...] = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )

    def __init__(self, color: Color):
        super().__init__(color=color, name="king", symbol="k")

    def get_pseudo_legal_moves(self, board: "Board", square: Square) -> Iterable[Square]:
        moves: List[Square] = []
        row, col = square
        for d_row, d_col in self._OFFSETS:
            target = (row + d_row, col + d_col)
            if not board.in_bounds(target):
                continue
            target_piece = board.get_piece(target)
            if target_piece is None or target_piece.color is not self.color:
                moves.append(target)
        return moves


class Pawn(Piece):
    def __init__(self, color: Color):
        super().__init__(color=color, name="pawn", symbol="p")

    def get_pseudo_legal_moves(self, board: "Board", square: Square) -> Iterable[Square]:
        moves: List[Square] = []
        row, col = square
        direction = self.color.pawn_direction

        one_forward = (row + direction, col)
        if board.in_bounds(one_forward) and board.get_piece(one_forward) is None:
            moves.append(one_forward)
            start_row = 6 if self.color is Color.WHITE else 1
            two_forward = (row + 2 * direction, col)
            if row == start_row and board.get_piece(two_forward) is None:
                moves.append(two_forward)

        for d_col in (-1, 1):
            target = (row + direction, col + d_col)
            if not board.in_bounds(target):
                continue
            target_piece = board.get_piece(target)
            if target_piece is not None and target_piece.color is not self.color:
                moves.append(target)

        # En passant handled at board layer because it requires board state.
        return moves


if TYPE_CHECKING:  # pragma: no cover - only for typing
    from .board import Board
else:  # pragma: no cover - not executed during runtime
    Board = "Board"  # type: ignore[assignment]
