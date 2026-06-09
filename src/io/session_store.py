"""JSON file I/O for calibration and results."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from src.config.settings import PROJECT
from src.domain.models import ScoreState


class SessionStore:
    """Persists calibration and run results."""

    def __init__(self, calibration_path: Path | None = None, results_path: Path | None = None) -> None:
        self.calibration_path = calibration_path or PROJECT.calibration_path
        self.results_path = results_path or PROJECT.results_path

    def save_calibration(self, input_offset_ms: int, audio_offset_ms: int) -> None:
        self.calibration_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "input_offset_ms": input_offset_ms,
            "audio_offset_ms": audio_offset_ms,
        }
        self.calibration_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_calibration(self) -> dict[str, int]:
        if not self.calibration_path.exists():
            return {"input_offset_ms": 0, "audio_offset_ms": 0}
        return json.loads(self.calibration_path.read_text(encoding="utf-8"))

    def save_results(self, score_state: ScoreState) -> None:
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(score_state)
        self.results_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

