"""Tests for persistence layer."""

import tempfile
import unittest
from pathlib import Path

from src.domain.models import ScoreState
from src.io.session_store import SessionStore


class TestSessionStore(unittest.TestCase):
    def test_save_and_load_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            store = SessionStore(
                calibration_path=base / "calibration.json",
                results_path=base / "results.json",
            )
            store.save_calibration(input_offset_ms=35, audio_offset_ms=-20)
            data = store.load_calibration()
            self.assertEqual(data["input_offset_ms"], 35)
            self.assertEqual(data["audio_offset_ms"], -20)

    def test_save_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            store = SessionStore(
                calibration_path=base / "calibration.json",
                results_path=base / "results.json",
            )
            state = ScoreState(score=1000, combo=6, max_combo=10, perfect_hits=4, good_hits=2, misses=1)
            store.save_results(state)
            self.assertTrue((base / "results.json").exists())


if __name__ == "__main__":
    unittest.main()

