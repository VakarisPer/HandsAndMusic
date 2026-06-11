"""Audio playback and manual chart creation tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
import sys

import pygame

AUDIO_FILE = "music/default.wav"
CHART_FILE = "data/manual_chart.json"


@dataclass
class ChartNote:
    lane: int
    time_seconds: float
    kind: str = "tap"


def _resolve_audio_file(audio_file: str | None = None) -> Path:
    return Path(audio_file) if audio_file else Path(AUDIO_FILE)


def _resolve_chart_file(chart_file: str | None = None) -> Path:
    return Path(chart_file) if chart_file else Path(CHART_FILE)


def play_audio(audio_file: str | None = None) -> float:
    resolved = str(_resolve_audio_file(audio_file))
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(resolved)
    pygame.mixer.music.play()
    return time.monotonic()


def get_current_time(start_time: float) -> float:
    return time.monotonic() - start_time


def stop_audio() -> None:
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()


def save_chart(notes: list[ChartNote], chart_file: str | None = None) -> Path:
    target = _resolve_chart_file(chart_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"audio_file": str(_resolve_audio_file()),
               "notes": [asdict(note) for note in notes]}
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[Chart] Saved {len(notes)} notes to {target}")
    return target


def load_chart(chart_file: str | None = None) -> list[ChartNote]:
    target = _resolve_chart_file(chart_file)
    if not target.exists():
        return []
    payload = json.loads(target.read_text(encoding="utf-8"))
    return [ChartNote(**raw) for raw in payload.get("notes", [])]


def chart_exists() -> bool:
    return _resolve_chart_file().exists()


def create_chart_live(audio_file: str | None = None,
                      chart_file: str | None = None) -> list[ChartNote]:
    """Record tile timings manually while listening to the song.

    Controls:
        1-5  — drop a note on that lane
        0    — drop a 5-lane chord
        U    — undo last note
        S    — save chart to disk
        Q    — save and quit
    """
    pygame.init()
    screen = pygame.display.set_mode((900, 240))
    pygame.display.set_caption("RhythmForge — Chart Creator")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small = pygame.font.Font(None, 26)

    resolved_audio = str(_resolve_audio_file(audio_file))
    resolved_chart = str(_resolve_chart_file(chart_file))

    notes = load_chart(chart_file)
    start_time = play_audio(audio_file)
    running = True

    while running:
        now = get_current_time(start_time)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    save_chart(notes, chart_file)
                    running = False
                elif event.key == pygame.K_u and notes:
                    notes.pop()
                elif event.key == pygame.K_s:
                    save_chart(notes, chart_file)
                elif event.key == pygame.K_0:
                    for lane in range(5):
                        notes.append(ChartNote(lane=lane,
                                               time_seconds=round(now, 4),
                                               kind="chord"))
                elif pygame.K_1 <= event.key <= pygame.K_5:
                    lane = event.key - pygame.K_1
                    notes.append(ChartNote(lane=lane,
                                           time_seconds=round(now, 4),
                                           kind="tap"))

        screen.fill((18, 18, 18))
        track = Path(resolved_audio).name[:40]
        header = font.render(track, True, (240, 240, 240))
        status = small.render(
            f"Time: {now:.2f}s  |  Notes: {len(notes)}", True, (200, 200, 200))
        hint1 = small.render(
            "1-5 lane  |  0 chord  |  U undo  |  S save  |  Q quit",
            True, (140, 140, 140))
        hint2 = small.render(
            "Chart saves to: " + resolved_chart, True, (100, 100, 120))
        screen.blit(header, (20, 20))
        screen.blit(status, (20, 70))
        screen.blit(hint1, (20, 120))
        screen.blit(hint2, (20, 160))
        pygame.display.flip()
        clock.tick(60)

    stop_audio()
    pygame.quit()
    return notes


if __name__ == "__main__":
    audio_arg = sys.argv[1] if len(sys.argv) > 1 else None
    create_chart_live(audio_file=audio_arg)
