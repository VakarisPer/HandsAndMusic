"""Manual charting helpers for tile spawn timing.

This module intentionally focuses on one thing:
you mark note timings yourself while listening to the song.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time

import pygame

AUDIO_FILE = "music/default.wav"
CHART_FILE = "data/manual_chart.json"


@dataclass
class ChartNote:
    lane: int
    time_seconds: float
    kind: str = "tap"


def _resolve_audio_file(audio_file: str | None = None) -> str:
    return str(Path(audio_file) if audio_file else Path(AUDIO_FILE))


def _resolve_chart_file(chart_file: str | None = None) -> Path:
    return Path(chart_file) if chart_file else Path(CHART_FILE)


def play_audio(audio_file: str | None = None) -> float:
    """Start playback and return monotonic start time."""
    resolved_file = _resolve_audio_file(audio_file)
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(resolved_file)
    pygame.mixer.music.play()
    print(f"[Audio] Playing: {resolved_file}")
    return time.monotonic()


def get_current_time(start_time: float) -> float:
    """Get elapsed seconds since playback start."""
    return time.monotonic() - start_time


def stop_audio() -> None:
    """Stop audio playback."""
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()


def save_chart(notes: list[ChartNote], chart_file: str | None = None) -> Path:
    """Save manual chart to JSON."""
    target = _resolve_chart_file(chart_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"audio_file": AUDIO_FILE, "notes": [asdict(note) for note in notes]}
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[Chart] Saved {len(notes)} notes to {target}")
    return target


def load_chart(chart_file: str | None = None) -> list[ChartNote]:
    """Load manual chart from JSON."""
    target = _resolve_chart_file(chart_file)
    if not target.exists():
        return []
    payload = json.loads(target.read_text(encoding="utf-8"))
    return [ChartNote(**raw) for raw in payload.get("notes", [])]


def create_chart_live(audio_file: str | None = None, chart_file: str | None = None) -> list[ChartNote]:
    """Create tile timings manually while song is playing.

    Controls:
    - `1..5`: add lane note now
    - `0`: add 5-lane chord now
    - `u`: undo last note
    - `s`: save chart
    - `q`: save and quit
    """
    pygame.init()
    screen = pygame.display.set_mode((900, 220))
    pygame.display.set_caption("Manual Tile Chart Creator")
    font = pygame.font.Font(None, 32)
    small = pygame.font.Font(None, 24)
    clock = pygame.time.Clock()

    notes = load_chart(chart_file)
    start_time = play_audio(audio_file)
    running = True

    while running:
        now = get_current_time(start_time)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_5:
                    lane = event.key - pygame.K_1
                    notes.append(ChartNote(lane=lane, time_seconds=round(now, 4), kind="tap"))
                elif event.key == pygame.K_0:
                    for lane in range(5):
                        notes.append(ChartNote(lane=lane, time_seconds=round(now, 4), kind="chord"))
                elif event.key == pygame.K_u and notes:
                    notes.pop()
                elif event.key == pygame.K_s:
                    save_chart(notes, chart_file)
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    save_chart(notes, chart_file)
                    running = False

        screen.fill((18, 18, 18))
        status = font.render(f"Time: {now:.2f}s | Notes: {len(notes)}", True, (240, 240, 240))
        hint = small.render("1-5 lane | 0 chord | U undo | S save | Q quit", True, (180, 180, 180))
        screen.blit(status, (20, 30))
        screen.blit(hint, (20, 80))
        pygame.display.flip()
        clock.tick(60)

    stop_audio()
    pygame.quit()
    return notes
