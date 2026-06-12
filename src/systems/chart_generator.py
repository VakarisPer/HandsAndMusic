"""Chart generation from beats."""

import random
from src.domain.models import ChartEvent, NoteKind


class ChartGenerator:
    def __init__(
        self,
        lane_count: int,
        seed: int = 11,
        chord_interval_beats: int = 16,
        golden_chance: float = 0.06,
    ) -> None:
        self.lane_count = lane_count
        self.seed = seed
        self.chord_interval_beats = chord_interval_beats
        self.golden_chance = golden_chance

    def generate(self, beats: list[float]) -> list[ChartEvent]:
        rng = random.Random(self.seed)
        events: list[ChartEvent] = []
        previous_lane = 0

        for idx, beat_time in enumerate(beats):
            if idx > 0 and idx % self.chord_interval_beats == 0:
                for lane in range(self.lane_count):
                    events.append(ChartEvent(
                        lane=lane, time_seconds=float(beat_time),
                        kind=NoteKind.CHORD,
                        is_golden=rng.random() < self.golden_chance))
                continue

            lane_pool = [lane for lane in range(self.lane_count) if lane != previous_lane]
            lane = rng.choice(lane_pool)
            previous_lane = lane
            events.append(ChartEvent(
                lane=lane, time_seconds=float(beat_time), kind=NoteKind.TAP,
                is_golden=rng.random() < self.golden_chance))
        return events
