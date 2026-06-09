"""Global runtime settings for deterministic gameplay."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WindowSettings:
    width: int = 1280
    height: int = 720
    title: str = "Hand-Gesture Rhythm Game"
    target_fps: int = 120


@dataclass(frozen=True)
class RhythmSettings:
    bpm: int = 120
    spawn_offset_seconds: float = 1.6
    song_duration_seconds: float = 120.0
    input_offset_ms: int = 0
    audio_offset_ms: int = 0
    perfect_window_ms: int = 60
    good_window_ms: int = 120
    miss_window_ms: int = 170

    @property
    def beat_interval(self) -> float:
        return 60.0 / self.bpm


@dataclass(frozen=True)
class GameplaySettings:
    lane_count: int = 5
    lane_spacing: int = 100
    note_size: int = 30
    receptor_size: int = 40
    receptor_y_padding: int = 100
    fall_pixels_per_second: float = 430.0
    chart_seed: int = 2026
    chord_interval_beats: int = 16
    hold_chance: float = 0.30
    double_note_chance: float = 0.18
    golden_note_chance: float = 0.06
    golden_note_points: int = 200


@dataclass(frozen=True)
class ProjectSettings:
    version: str = "0.1.0"
    default_audio_file: str = "music/default.wav"
    calibration_path: Path = Path("data") / "calibration.json"
    results_path: Path = Path("data") / "results.json"


WINDOW = WindowSettings()
RHYTHM = RhythmSettings()
GAMEPLAY = GameplaySettings()
PROJECT = ProjectSettings()

GESTURE_TO_LANE = {
    "Closed_Fist": 0,
    "Open_Palm": 1,
    "Pointing_Up": 2,
    "Thumb_Up": 3,
    "Victory": 4,
}

