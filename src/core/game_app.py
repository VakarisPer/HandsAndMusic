"""Main game orchestration class."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pygame

from src.config.settings import GAMEPLAY, RHYTHM, WINDOW
from src.core.factory import SystemFactory
from src.core.state_machine import StateMachine
from src.domain.models import ChartEvent, HitFeedback, LaneReceptor, Note, NoteKind
from src.systems.beat_grid import BeatGrid
from src.systems.chart_generator import ChartGenerator
from src.systems.song_analyzer import analyze_song
from src.systems.particles import ParticleSystem


class GameApp:
    """Coordinates all game systems while keeping concerns separated."""

    def __init__(self, factory: SystemFactory | None = None,
                 audio_file: str | None = None,
                 level_name: str = "",
                 volume: float = 1.0) -> None:
        self.factory = factory or SystemFactory()
        self.state_machine = StateMachine()
        self.store = self.factory.create_session_store()
        calibration = self.store.load_calibration()

        level_path = Path("levels") / f"{level_name}.json"
        level_data = None
        if level_name and level_path.exists():
            level_data = json.loads(level_path.read_text(encoding="utf-8"))

        # Determine audio: level's file overrides settings
        resolved_audio = audio_file
        if level_data is not None:
            lvl_audio = self._resolve_level_audio(level_data.get("audio_file", ""))
            if lvl_audio:
                resolved_audio = lvl_audio

        self.audio_clock = self.factory.create_audio_clock(
            audio_file=resolved_audio, volume=volume)
        self.input_system = self.factory.create_input_system()
        self.render_system = None
        self.spawn_system = self.factory.create_spawn_system()
        self.score_system = self.factory.create_score_system()
        self.timing_judge = self.factory.create_timing_judge(calibration["input_offset_ms"])
        self.hand_adapter = self.factory.create_hand_adapter()
        self.audio_offset_ms = calibration["audio_offset_ms"]
        self.particles = ParticleSystem()

        if level_data is not None:
            raw_notes = level_data.get("notes", [])
            self.chart_events = []
            for n in raw_notes:
                kind = NoteKind.CHORD if n.get("kind") == "chord" else NoteKind.TAP
                self.chart_events.append(ChartEvent(
                    lane=n["lane"], time_seconds=n["time_seconds"], kind=kind,
                    is_golden=random.random() < GAMEPLAY.golden_note_chance))
            self._song_duration = (max(e.time_seconds for e in self.chart_events) + 5.0) \
                if self.chart_events else RHYTHM.song_duration_seconds
            print(f"[Game] Loaded level '{level_name}': {len(self.chart_events)} notes")
        else:
            analysis = analyze_song(resolved_audio) if resolved_audio else None
            if analysis is not None:
                beats, self._song_duration = analysis
            else:
                beat_grid = BeatGrid(bpm=RHYTHM.bpm, duration_seconds=RHYTHM.song_duration_seconds)
                beats = beat_grid.generate_beats().tolist()
                self._song_duration = RHYTHM.song_duration_seconds
            self.chart_events = ChartGenerator(
                lane_count=GAMEPLAY.lane_count,
                seed=GAMEPLAY.chart_seed,
                chord_interval_beats=GAMEPLAY.chord_interval_beats,
                golden_chance=GAMEPLAY.golden_note_chance,
            ).generate(beats)
        self.notes: list[Note] = []
        self._previous_active_lanes: set[int] = set()
        self._receptor_feedback_colors: dict[int, tuple[int, int, int]] = {
            lane: (255, 255, 255) for lane in range(GAMEPLAY.lane_count)
        }
        self._catch_particles: list[tuple[float, float, tuple, bool]] = []
        self._hit_feedbacks: list[HitFeedback] = []

    @staticmethod
    def _resolve_level_audio(audio_file: str) -> str | None:
        """Resolve a level's audio path, tolerating levels recorded on
        another machine (absolute paths) by falling back to the filename
        in the local music/ and audio/ folders."""
        if not audio_file:
            return None
        if Path(audio_file).exists():
            return audio_file
        filename = Path(audio_file).name
        for folder in ("music", "audio"):
            candidate = Path(folder) / filename
            if candidate.exists():
                return str(candidate)
        return None

    def _build_lane_positions(self, screen_width: int) -> list[float]:
        center_x = screen_width / 2
        return [center_x + (lane - 2) * GAMEPLAY.lane_spacing for lane in range(GAMEPLAY.lane_count)]

    def _build_receptors(self, lane_positions: list[float], screen_height: int) -> list[LaneReceptor]:
        receptors: list[LaneReceptor] = []
        for lane, x in enumerate(lane_positions):
            receptors.append(
                LaneReceptor(
                    lane=lane,
                    x=x - 5,
                    y=screen_height - GAMEPLAY.receptor_y_padding,
                    size=GAMEPLAY.receptor_size,
                )
            )
        return receptors

    def run(self, username: str = "Player") -> tuple[int, int]:
        pygame.init()
        screen = pygame.display.set_mode((WINDOW.width, WINDOW.height),
                                         pygame.RESIZABLE | pygame.SCALED)
        pygame.display.set_caption(f"Hands & Music - {username}")
        clock = pygame.time.Clock()
        self.render_system = self.factory.create_render_system()
        self.render_system.particle_system = self.particles
        lane_positions = self._build_lane_positions(screen.get_width())
        receptors = self._build_receptors(lane_positions, screen.get_height())

        self.state_machine.start()
        self.audio_clock.start(offset_ms=self.audio_offset_ms)
        running = True

        while running:
            dt = clock.tick(WINDOW.target_fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.state_machine.pause_toggle()

            if self.state_machine.state.name == "PAUSED":
                pygame.display.flip()
                continue

            current_time = self.audio_clock.current_time()
            self.notes.extend(self.spawn_system.spawn_due_notes(self.chart_events, current_time))

            for note in self.notes:
                note.update(dt, GAMEPLAY.fall_pixels_per_second)

            gestures, pointer_positions = self.hand_adapter.poll_snapshot()
            active_pointer_lanes = self._pointer_collision_lanes(pointer_positions, receptors, screen)
            active_lanes = active_pointer_lanes | self.input_system.lanes_from_keyboard()
            newly_pressed_lanes = active_lanes - self._previous_active_lanes
            self._resolve_pointer_hits(newly_pressed_lanes, current_time, receptors, lane_positions)
            self._handle_open_palm_chords(gestures, current_time, receptors, lane_positions)
            self._resolve_misses(receptors, lane_positions)
            self._previous_active_lanes = active_lanes

            self._spawn_catch_particles(lane_positions)

            self.render_system.draw_frame(
                screen=screen,
                notes=self.notes,
                receptors=receptors,
                lane_positions=lane_positions,
                score_state=self.score_system.state,
                active_lanes=active_lanes,
                pointer_positions=pointer_positions,
                receptor_feedback_colors=self._receptor_feedback_colors,
                hit_feedbacks=self._hit_feedbacks,
                camera_frame=self.hand_adapter.get_frame(),
                delta_time=dt,
            )
            self._hit_feedbacks.clear()
            pygame.display.flip()

            if current_time > self._song_duration and not self.notes:
                running = False

        score = self.score_system.state.score
        max_combo = self.score_system.state.max_combo

        self.audio_clock.stop()
        self.hand_adapter.shutdown()
        pygame.quit()
        return score, max_combo

    def _resolve_pointer_hits(self, active_lanes: set[int], current_time: float,
                              receptors: list[LaneReceptor],
                              lane_positions: list[float]) -> None:
        self._resolve_catches(active_lanes, current_time, receptors,
                              lane_positions, chords_only=False,
                              catch_color=(255, 255, 255))

    def _handle_open_palm_chords(self, gestures: list[str], current_time: float,
                                 receptors: list[LaneReceptor],
                                 lane_positions: list[float]) -> None:
        if "Open_Palm" not in gestures:
            return
        self._resolve_catches(set(range(GAMEPLAY.lane_count)), current_time,
                              receptors, lane_positions, chords_only=True,
                              catch_color=(180, 100, 255))

    def _resolve_catches(self, active_lanes: set[int], current_time: float,
                         receptors: list[LaneReceptor],
                         lane_positions: list[float],
                         chords_only: bool,
                         catch_color: tuple[int, int, int]) -> None:
        catcher_had_tiles_available: set[int] = set()
        catcher_caught_tiles_this_frame: set[int] = set()

        for lane in active_lanes:
            receptor = receptors[lane]
            catchable = [
                n for n in self.notes
                if n.lane == lane and not n.judged
                and (not chords_only or n.kind == NoteKind.CHORD)
                and abs((n.y + GAMEPLAY.note_size / 2) - (receptor.y + receptor.size / 2)) <= 75
            ]
            if not catchable:
                continue
            catcher_had_tiles_available.add(lane)
            note = min(catchable, key=lambda n: abs(n.scheduled_time - current_time))
            judgement = self.timing_judge.classify(current_time, note.scheduled_time)
            if judgement in {"perfect", "good", "late"}:
                note.judged = True
                note.hit_time = current_time
                catcher_caught_tiles_this_frame.add(lane)
                self.score_system.apply_judgement(judgement, is_golden=note.is_golden)
                self._hit_feedbacks.append(HitFeedback(
                    x=lane_positions[lane] + GAMEPLAY.note_size / 2,
                    y=receptor.y - 60,
                    judgement=judgement,
                ))
                self._catch_particles.append((
                    lane_positions[lane] + 15, note.y + 15,
                    (255, 215, 0) if note.is_golden else catch_color,
                    note.is_golden,
                ))

        self.notes = [note for note in self.notes if not note.judged]
        self._apply_feedback(
            catcher_used_this_frame=set(active_lanes),
            catcher_had_tiles_available=catcher_had_tiles_available,
            catcher_caught_tiles_this_frame=catcher_caught_tiles_this_frame,
        )

    def _resolve_misses(self, receptors: list[LaneReceptor],
                         lane_positions: list[float]) -> None:
        remaining: list[Note] = []
        for note in self.notes:
            receptor = receptors[note.lane]
            miss_threshold = receptor.y + receptor.size + 30
            if note.y >= miss_threshold:
                self.score_system.apply_judgement("miss")
                self._hit_feedbacks.append(HitFeedback(
                    x=lane_positions[note.lane] + GAMEPLAY.note_size / 2,
                    y=receptor.y + receptor.size / 2,
                    judgement="miss",
                ))
                continue
            remaining.append(note)
        self.notes = remaining

    def _spawn_catch_particles(self, lane_positions: list[float]) -> None:
        for x, y, color, is_golden in self._catch_particles:
            if is_golden:
                self.particles.emit(x, y, (255, 215, 0),
                                    count=24, speed_min=60, speed_max=250,
                                    size_min=2, size_max=7, lifetime=1.0)
                self.particles.emit(x, y, (255, 240, 100),
                                    count=12, speed_min=20, speed_max=100,
                                    size_min=1, size_max=3, lifetime=0.6)
            else:
                self.particles.emit(x, y, color,
                                    count=12, speed_min=40, speed_max=180,
                                    size_min=1.5, size_max=5, lifetime=0.8)
        self._catch_particles.clear()

    def _pointer_collision_lanes(
        self,
        pointer_positions: list[tuple[float, float]],
        receptors: list[LaneReceptor],
        screen: pygame.Surface,
    ) -> set[int]:
        active_lanes: set[int] = set()
        for normalized_x, normalized_y in pointer_positions:
            px = normalized_x * screen.get_width()
            py = normalized_y * screen.get_height()
            for receptor in receptors:
                cx = receptor.x + receptor.size / 2
                cy = receptor.y + receptor.size / 2
                if ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 <= 40:
                    active_lanes.add(receptor.lane)
        return active_lanes

    def _apply_feedback(
        self,
        catcher_used_this_frame: set[int],
        catcher_had_tiles_available: set[int],
        catcher_caught_tiles_this_frame: set[int],
    ) -> None:
        for lane in range(GAMEPLAY.lane_count):
            self._receptor_feedback_colors[lane] = (255, 255, 255)

        for lane in catcher_used_this_frame:
            if lane in catcher_caught_tiles_this_frame:
                self._receptor_feedback_colors[lane] = (0, 255, 0)
            elif lane in catcher_had_tiles_available:
                self._receptor_feedback_colors[lane] = (255, 0, 0)
            else:
                self._receptor_feedback_colors[lane] = (255, 255, 255)
