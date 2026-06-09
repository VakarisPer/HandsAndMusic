"""Factory Method pattern for runtime component creation."""

from src.audio.audio_clock import AudioClock
from src.config.settings import PROJECT, RHYTHM
from src.io.session_store import SessionStore
from src.systems.input_system import InputSystem
from src.systems.render_system import RenderSystem
from src.systems.scoring_system import ScoreSystem
from src.systems.spawn_system import SpawnSystem
from src.systems.timing_judge import TimingJudge, TimingWindows
from src.vision.hand_tracker_adapter import HandTrackerAdapter


class SystemFactory:
    """Factory Method implementation for game runtime systems."""

    def create_audio_clock(self, audio_file: str | None = None) -> AudioClock:
        return AudioClock(audio_file=audio_file or PROJECT.default_audio_file)

    def create_input_system(self, gesture_map: dict[str, int]) -> InputSystem:
        return InputSystem(gesture_map=gesture_map)

    def create_render_system(self) -> RenderSystem:
        return RenderSystem()

    def create_spawn_system(self) -> SpawnSystem:
        return SpawnSystem(spawn_offset_seconds=RHYTHM.spawn_offset_seconds)

    def create_score_system(self) -> ScoreSystem:
        return ScoreSystem()

    def create_timing_judge(self, input_offset_ms: int) -> TimingJudge:
        windows = TimingWindows(
            perfect_ms=RHYTHM.perfect_window_ms,
            good_ms=RHYTHM.good_window_ms,
            miss_ms=RHYTHM.miss_window_ms,
        )
        return TimingJudge(windows=windows, input_offset_ms=input_offset_ms)

    def create_hand_adapter(self) -> HandTrackerAdapter:
        return HandTrackerAdapter()

    def create_session_store(self) -> SessionStore:
        return SessionStore()

