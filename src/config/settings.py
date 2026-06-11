"""Global runtime settings for deterministic gameplay."""

import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WindowSettings:
    width: int = 1280
    height: int = 720
    title: str = "Hand-Gesture Rhythm Game"
    target_fps: int = 60


@dataclass(frozen=True)
class RhythmSettings:
    bpm: int = 120
    spawn_offset_seconds: float = 1.6
    song_duration_seconds: float = 120.0
    perfect_window_ms: int = 60
    good_window_ms: int = 120
    late_window_ms: int = 170


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
    double_note_chance: float = 0.18
    golden_note_chance: float = 0.06
    golden_note_points: int = 100


@dataclass(frozen=True)
class ProjectSettings:
    version: str = "0.1.4"
    default_audio_file: str = "music/default.wav"
    calibration_path: Path = Path("data") / "calibration.json"
    results_path: Path = Path("data") / "results.json"
    font_path: str = "fonts/RobotikaPixelGreek-nAWJR.otf"
    scores_file: str = "data/scores.json"


WINDOW = WindowSettings()
RHYTHM = RhythmSettings()
GAMEPLAY = GameplaySettings()
PROJECT = ProjectSettings()

HAND_DETECTION_CONFIDENCE = 0.6
HAND_TRACKING_CONFIDENCE = 0.55
HAND_CAMERA_WIDTH =  640
HAND_CAMERA_HEIGHT = 480
HAND_MODEL_COMPLEXITY = 0

# ---------------------------------------------------------------------------
# Legacy GameConfig – consumed by menu.py / main.py for UI and runtime state
# ---------------------------------------------------------------------------

class GameConfig:
    """Mutable application config with UI colors, runtime state, and helpers.

    Delegates to the frozen dataclasses above for gameplay values so the
    game engine and menu layer share a single source of truth.
    """

    # -- window / display ---------------------------------------------------
    SCREEN_WIDTH = WINDOW.width
    SCREEN_HEIGHT = WINDOW.height
    SCREEN_FPS = WINDOW.target_fps

    # -- runtime state (mutable) --------------------------------------------
    AUDIO_FILE: str = ""
    USERNAME: str = ""
    SELECTED_LEVEL: str = ""
    MUSIC_VOLUME: float = 0.7

    # -- paths --------------------------------------------------------------
    FONT_PATH: str = PROJECT.font_path
    SCORES_FILE: str = PROJECT.scores_file

    # -- base colours -------------------------------------------------------
    COLOR_BLACK = (0, 0, 0)
    COLOR_GREEN = (0, 255, 0)

    # -- UI panel & accent --------------------------------------------------
    UI_PANEL = (15, 15, 35, 230)
    UI_ACCENT = (80, 180, 255)
    UI_BUTTON_START = (34, 180, 74)
    UI_BUTTON_DISABLED = (60, 60, 70)
    UI_BUTTON_EXIT = (200, 55, 55)
    UI_BUTTON_SETTINGS = (55, 55, 200)
    UI_SLIDER_TRACK = (50, 50, 70)
    UI_SLIDER_FILL = (80, 180, 255)
    UI_SLIDER_KNOB = (230, 230, 245)
    UI_TEXT_PRIMARY = (245, 245, 255)
    UI_TEXT_SECONDARY = (160, 175, 195)
    UI_TEXT_WARN = (255, 140, 100)

    # -- leaderboard --------------------------------------------------------
    LEADERBOARD_BG = (10, 10, 30, 220)
    LEADERBOARD_BORDER = (60, 60, 120)
    LEADERBOARD_ROW_BG = (18, 18, 38, 180)
    LEADERBOARD_ROW_ALT = (22, 22, 42, 180)
    LEADERBOARD_GOLD = (255, 215, 0)
    LEADERBOARD_GOLD_BG = (50, 40, 10, 220)
    LEADERBOARD_SILVER = (192, 192, 192)
    LEADERBOARD_SILVER_BG = (35, 35, 40, 200)
    LEADERBOARD_BRONZE = (205, 127, 50)
    LEADERBOARD_BRONZE_BG = (40, 28, 12, 200)

    # -- username input -----------------------------------------------------
    USERNAME_INPUT_BG = (18, 18, 40)
    USERNAME_INPUT_BORDER = (60, 60, 140)
    USERNAME_INPUT_FOCUS_BORDER = (100, 180, 255)
    USERNAME_INPUT_TEXT = (220, 220, 255)
    USERNAME_INPUT_PLACEHOLDER = (80, 80, 120)
    USERNAME_INPUT_CURSOR = (100, 180, 255)

    # -- in-game score display ----------------------------------------------
    SCORE_DISPLAY_COMBO = (255, 200, 60)

    @staticmethod
    def rainbow_color(t, saturation=1.0, brightness=1.0):
        r = int((math.sin(t) * 0.5 + 0.5) * 255 * brightness * saturation)
        g = int((math.sin(t + 2.094) * 0.5 + 0.5) * 255 * brightness * saturation)
        b = int((math.sin(t + 4.189) * 0.5 + 0.5) * 255 * brightness * saturation)
        return (r, g, b)
