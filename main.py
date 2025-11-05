"""Entrypoint para jugar al ajedrez desde la terminal."""
from chess_game import Game


def main() -> None:
    Game().play()


if __name__ == "__main__":
    main()
