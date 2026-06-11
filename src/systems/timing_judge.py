"""Timing judgement system."""

from dataclasses import dataclass

@dataclass(frozen=True)
class TimingWindows:
    perfect_ms: int
    good_ms: int
    late_ms: int

class TimingJudge:
    """Classifies input accuracy against note scheduled time."""

    def __init__(self, windows: TimingWindows, input_offset_ms: int = 0) -> None:
        self.windows = windows
        self.input_offset_seconds = input_offset_ms / 1000.0

    def classify(self, current_time: float, scheduled_time: float) -> str:
        signed_delta_ms = (current_time + self.input_offset_seconds - scheduled_time) * 1000.0
        delta_ms = abs(signed_delta_ms)
        if signed_delta_ms < -self.windows.late_ms:
            return "too_early"
        if delta_ms <= self.windows.perfect_ms:
            return "perfect"
        if delta_ms <= self.windows.good_ms:
            return "good"
        return "late"

