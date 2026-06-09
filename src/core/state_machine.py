"""Game state machine."""

from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    RESULTS = auto()

class StateMachine:
    """Keeps state transitions explicit and centralized."""

    def __init__(self) -> None:
        self.state = GameState.MENU

    def start(self) -> None:
        self.state = GameState.PLAYING

    def pause_toggle(self) -> None:
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def finish(self) -> None:
        self.state = GameState.RESULTS