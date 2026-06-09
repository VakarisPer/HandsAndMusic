"""Tests for rhythm core systems."""

import unittest

from src.domain.models import ChartEvent, NoteKind
from src.systems.beat_grid import BeatGrid
from src.systems.scoring_system import ScoreSystem
from src.systems.spawn_system import SpawnSystem
from src.systems.timing_judge import TimingJudge, TimingWindows


class TestRhythmSystems(unittest.TestCase):
    def test_beat_grid_interval(self) -> None:
        grid = BeatGrid(bpm=120, duration_seconds=2.1)
        beats = grid.generate_beats().tolist()
        self.assertAlmostEqual(grid.interval_seconds, 0.5)
        self.assertEqual(beats, [0.0, 0.5, 1.0, 1.5, 2.0])

    def test_spawn_system_uses_offset(self) -> None:
        events = [
            ChartEvent(lane=0, time_seconds=1.0, kind=NoteKind.TAP),
            ChartEvent(lane=1, time_seconds=1.5, kind=NoteKind.HOLD),
        ]
        system = SpawnSystem(spawn_offset_seconds=0.5)
        notes = system.spawn_due_notes(events, current_time=0.4)
        self.assertEqual(len(notes), 0)
        notes = system.spawn_due_notes(events, current_time=0.5)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].lane, 0)

    def test_timing_judge_windows(self) -> None:
        judge = TimingJudge(TimingWindows(perfect_ms=60, good_ms=120, miss_ms=170))
        self.assertEqual(judge.classify(1.01, 1.0), "perfect")
        self.assertEqual(judge.classify(1.10, 1.0), "good")
        self.assertEqual(judge.classify(1.16, 1.0), "miss")
        self.assertEqual(judge.classify(1.25, 1.0), "late")
        self.assertEqual(judge.classify(0.70, 1.0), "too_early")

    def test_score_combo_and_accuracy(self) -> None:
        scoring = ScoreSystem()
        scoring.apply_judgement("perfect")
        scoring.apply_judgement("good")
        scoring.apply_judgement("miss")
        self.assertEqual(scoring.state.combo, 0)
        self.assertEqual(scoring.state.max_combo, 2)
        self.assertGreater(scoring.accuracy_percent(), 0.0)


if __name__ == "__main__":
    unittest.main()

