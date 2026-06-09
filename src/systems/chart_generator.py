"""Chart generation from beats."""

import random
from src.domain.models import ChartEvent, NoteKind

class ChartGenerator:
    """Creates lane events from beat timestamps."""

    def __init__(
        self,
        lane_count: int,
        seed: int = 11,
        chord_interval_beats: int = 16,
        hold_chance: float = 0.30,
        double_note_chance: float = 0.18,
    ) -> None:
        self.lane_count = lane_count
        self.seed = seed
        self.chord_interval_beats = chord_interval_beats
        self.hold_chance = hold_chance
        self.double_note_chance = double_note_chance

    def generate(self, beats: list[float]) -> list[ChartEvent]:
        rng = random.Random(self.seed)
        events: list[ChartEvent] = []
        previous_lane = 0

        for idx, beat_time in enumerate(beats):
            if idx > 0 and idx % self.chord_interval_beats == 0:
                for lane in range(self.lane_count):
                    events.append(ChartEvent(lane=lane, time_seconds=float(beat_time), kind=NoteKind.CHORD))
                continue

            lane_pool = [lane for lane in range(self.lane_count) if lane != previous_lane]
            lane = rng.choice(lane_pool)
            previous_lane = lane
            kind = NoteKind.HOLD if rng.random() < self.hold_chance else NoteKind.TAP
            events.append(ChartEvent(lane=lane, time_seconds=float(beat_time), kind=kind))

            # Extra variation while staying locked to beat grid time.
            if rng.random() < self.double_note_chance and idx % 2 == 0:
                extra_lane_pool = [value for value in range(self.lane_count) if value != lane]
                extra_lane = rng.choice(extra_lane_pool)
                extra_kind = NoteKind.HOLD if rng.random() < self.hold_chance else NoteKind.TAP
                events.append(ChartEvent(lane=extra_lane, time_seconds=float(beat_time), kind=extra_kind))
        return events

