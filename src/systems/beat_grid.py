"""BPM-based beat timeline generation."""

import numpy as np


class BeatGrid:
    """Generates deterministic beat positions from BPM."""

    def __init__(self, bpm: int, duration_seconds: float) -> None:
        self.bpm = bpm
        self.duration_seconds = duration_seconds

    @property
    def interval_seconds(self) -> float:
        return 60.0 / self.bpm

    def generate_beats(self) -> np.ndarray:
        return np.arange(0.0, self.duration_seconds, self.interval_seconds, dtype=float)

