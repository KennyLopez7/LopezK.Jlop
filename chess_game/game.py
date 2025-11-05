"""High level interface for playing chess in the terminal."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .board import Board, Move, notation_to_square, square_to_notation
from .pieces import Color, Piece


@dataclass
class MoveResult:
    """Result of attempting to make a move."""

    move: Move
    captured: Optional[Piece]
    note: Optional[str] = None


class Game:
    """Encapsulates a full chess game with a simple text UI."""

    def __init__(self) -> None:
        self.board = Board()

    # ------------------------------------------------------------------
    # Gameplay
    # ------------------------------------------------------------------
    @property
    def turn(self) -> Color:
        return self.board.turn

    def legal_moves(self) -> Iterable[Move]:
        return self.board.generate_legal_moves()

    def move_from_string(self, text: str) -> MoveResult:
        move = self._parse_move(text)
        captured = self.board.get_piece(move.end)
        if move.is_en_passant:
            captured = self.board.get_piece((move.start[0], move.end[1]))
        self.board.apply_move(move)
        result = self.board.result()
        return MoveResult(move=move, captured=captured, note=result)

    def _parse_move(self, text: str) -> Move:
        text = text.strip()
        if text in {"O-O", "0-0", "o-o"}:
            return self._castle(True)
        if text in {"O-O-O", "0-0-0", "o-o-o"}:
            return self._castle(False)

        if len(text) not in {4, 5}:
            raise ValueError("Expected coordinate move like e2e4 or e7e8q")

        start = notation_to_square(text[:2])
        end = notation_to_square(text[2:4])
        promotion = text[4].lower() if len(text) == 5 else None
        candidate = Move(start=start, end=end, promotion=promotion)

        legal_moves = list(self.board.generate_legal_moves(self.turn))
        for move in legal_moves:
            if (
                move.start == candidate.start
                and move.end == candidate.end
                and (move.promotion or None) == (promotion or None)
            ):
                return move
        raise ValueError("Illegal move")

    def _castle(self, king_side: bool) -> Move:
        legal_moves = list(self.board.generate_legal_moves(self.turn))
        row = 7 if self.turn is Color.WHITE else 0
        target_col = 6 if king_side else 2
        for move in legal_moves:
            if move.is_castling and move.end == (row, target_col):
                return move
        side = "king" if king_side else "queen"
        raise ValueError(f"Castling to the {side} side is not legal right now")

    def status(self) -> str:
        note = self.board.result()
        if note:
            return note
        return f"{self.turn.value.capitalize()} to move"

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def board_text(self) -> str:
        return str(self.board)

    def legal_moves_for_square(self, square_notation: str) -> str:
        square = notation_to_square(square_notation)
        moves = [
            move
            for move in self.board.generate_legal_moves(self.turn)
            if move.start == square
        ]
        if not moves:
            return "No legal moves"
        move_list = ", ".join(square_to_notation(move.end) for move in moves)
        return f"Legal moves for {square_notation}: {move_list}"

    # ------------------------------------------------------------------
    # Interactive loop
    # ------------------------------------------------------------------
    def play(self) -> None:  # pragma: no cover - manual interaction
        print("Bienvenido al ajedrez! Usa movimientos como e2e4 o escribe 'help'.")
        while True:
            print(self.board_text())
            print(self.status())
            command = input("> ").strip()
            if command.lower() in {"quit", "salir", "exit"}:
                print("Juego terminado.")
                return
            if command.lower() in {"help", "ayuda"}:
                self._print_help()
                continue
            if command.lower().startswith("moves "):
                _, square = command.split(maxsplit=1)
                try:
                    print(self.legal_moves_for_square(square))
                except Exception as exc:  # pylint: disable=broad-except
                    print(f"Error: {exc}")
                continue
            try:
                result = self.move_from_string(command)
            except Exception as exc:  # pylint: disable=broad-except
                print(f"Error: {exc}")
                continue
            if result.note:
                print(result.note)
                print(self.board_text())
                return

    def _print_help(self) -> None:  # pragma: no cover - manual interaction helper
        print(
            "Comandos disponibles:\n"
            "  e2e4          - realiza un movimiento\n"
            "  e7e8q         - realiza una promoción\n"
            "  O-O / O-O-O   - enroque\n"
            "  moves e2      - muestra movimientos legales desde una casilla\n"
            "  quit          - salir"
        )
