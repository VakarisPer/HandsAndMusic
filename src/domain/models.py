"""Gameplay domain models."""

from dataclasses import dataclass, field
from enum import Enum


class NoteKind(str, Enum):
    TAP = "tap"
    CHORD = "chord"


@dataclass
class ChartEvent:
    lane: int
    time_seconds: float
    kind: NoteKind = NoteKind.TAP
    is_golden: bool = False


@dataclass
class Note:
    lane: int
    scheduled_time: float
    y: float
    kind: NoteKind = NoteKind.TAP
    judged: bool = False
    spawned: bool = False
    is_golden: bool = False
    hit_time: float | None = None

    def update(self, dt: float, pixels_per_second: float) -> None:
        self.y += dt * pixels_per_second


@dataclass
class LaneReceptor:
    lane: int
    x: float
    y: float
    size: int


@dataclass
class ScoreState:
    score: int = 0
    combo: int = 0
    max_combo: int = 0
    perfect_hits: int = 0
    good_hits: int = 0
    misses: int = 0
    history: list[str] = field(default_factory=list)


@dataclass
class HitFeedback:
    x: float
    y: float
    judgement: str

