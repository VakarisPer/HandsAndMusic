"""Regression tests for deterministic schedule behavior."""

import unittest

from src.systems.beat_grid import BeatGrid
from src.systems.chart_generator import ChartGenerator


class TestDeterminism(unittest.TestCase):
    def test_same_bpm_and_duration_produces_same_chart(self) -> None:
        beats_a = BeatGrid(bpm=120, duration_seconds=8.0).generate_beats().tolist()
        beats_b = BeatGrid(bpm=120, duration_seconds=8.0).generate_beats().tolist()
        chart_gen = ChartGenerator(lane_count=5)
        chart_a = chart_gen.generate(beats_a)
        chart_b = chart_gen.generate(beats_b)

        serial_a = [(e.lane, e.time_seconds, e.kind.value) for e in chart_a]
        serial_b = [(e.lane, e.time_seconds, e.kind.value) for e in chart_b]
        self.assertEqual(serial_a, serial_b)

if __name__ == "__main__":
    unittest.main()