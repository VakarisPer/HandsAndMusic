"""Deterministic audio clock."""

from dataclasses import dataclass
from pathlib import Path
import time
import pygame


@dataclass
class AudioClock:
    """Authoritative song clock based on playback start time."""

    audio_file: str
    volume: float = 1.0
    _start_time: float | None = None
    _offset_seconds: float = 0.0

    def start(self, offset_ms: int = 0) -> None:
        self._offset_seconds = offset_ms / 1000.0
        if Path(self.audio_file).exists():
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(self.audio_file)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
        self._start_time = time.monotonic()

    def stop(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self._start_time = None

    def current_time(self) -> float:
        if self._start_time is None:
            return 0.0
        return max(0.0, time.monotonic() - self._start_time + self._offset_seconds)

