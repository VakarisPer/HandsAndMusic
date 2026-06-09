"""Project entrypoint."""

from src.core.game_app import GameApp


def main() -> None:
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()