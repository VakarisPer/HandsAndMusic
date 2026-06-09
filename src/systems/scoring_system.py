"""Score and combo management."""

from src.domain.models import ScoreState


class ScoreSystem:
    def __init__(self, state: ScoreState | None = None) -> None:
        self.state = state or ScoreState()

    def apply_judgement(self, judgement: str) -> None:
        if judgement == "perfect":
            self.state.score += 10 * max(1, self.state.combo)
            self.state.combo += 1
            self.state.perfect_hits += 1
        elif judgement == "good":
            self.state.score += 5 * max(1, self.state.combo)
            self.state.combo += 1
            self.state.good_hits += 1
        else:
            self.state.score = max(0, self.state.score - 5)
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
