"""Score and combo management."""

from src.config.settings import GAMEPLAY
from src.domain.models import ScoreState

class ScoreSystem:
    def __init__(self, state: ScoreState | None = None) -> None:
        self.state = state or ScoreState()

    def apply_judgement(self, judgement: str, is_golden: bool = False) -> None:
        if judgement == "perfect":
            self.state.score += 10
            if is_golden:
                self.state.score += GAMEPLAY.golden_note_points
            self.state.combo += 1
            self.state.perfect_hits += 1
        elif judgement == "good":
            self.state.score += 5
            if is_golden:
                self.state.score += GAMEPLAY.golden_note_points
            self.state.combo += 1
            self.state.good_hits += 1
        elif judgement in ("late", "miss"):
            self.state.score = max(0, self.state.score - 5)
            self.state.combo = 0
            self.state.misses += 1
        else:
            self.state.combo = 0
            self.state.misses += 1
        self.state.max_combo = max(self.state.max_combo, self.state.combo)
        self.state.history.append(judgement)

    def accuracy_percent(self) -> float:
        total = self.state.perfect_hits + self.state.good_hits + self.state.misses
        if total == 0:
            return 0.0
        weighted = self.state.perfect_hits + 0.6 * self.state.good_hits
        return round((weighted / total) * 100.0, 2)
