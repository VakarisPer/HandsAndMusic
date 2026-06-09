"""Main game orchestration class."""

from __future__ import annotations

import pygame

from src.config.settings import GAMEPLAY, GESTURE_TO_LANE, RHYTHM, WINDOW
from src.core.factory import SystemFactory
from src.core.state_machine import StateMachine
from src.domain.models import LaneReceptor, Note, NoteKind
from src.systems.beat_grid import BeatGrid
from src.systems.chart_generator import ChartGenerator


class GameApp:
    """Coordinates all game systems while keeping concerns separated."""

    def __init__(self, factory: SystemFactory | None = None) -> None:
        self.factory = factory or SystemFactory()
        self.state_machine = StateMachine()
        self.store = self.factory.create_session_store()
        calibration = self.store.load_calibration()

        self.audio_clock = self.factory.create_audio_clock()
        self.input_system = self.factory.create_input_system(GESTURE_TO_LANE)
        self.render_system = None
        self.spawn_system = self.factory.create_spawn_system()
        self.score_system = self.factory.create_score_system()
        self.timing_judge = self.factory.create_timing_judge(calibration["input_offset_ms"])
        self.hand_adapter = self.factory.create_hand_adapter()
        self.audio_offset_ms = calibration["audio_offset_ms"]

        beat_grid = BeatGrid(bpm=RHYTHM.bpm, duration_seconds=RHYTHM.song_duration_seconds)
        self.chart_events = ChartGenerator(
            lane_count=GAMEPLAY.lane_count,
            seed=GAMEPLAY.chart_seed,
            chord_interval_beats=GAMEPLAY.chord_interval_beats,
            hold_chance=GAMEPLAY.hold_chance,
            double_note_chance=GAMEPLAY.double_note_chance,
        ).generate(beat_grid.generate_beats().tolist())
        self.notes: list[Note] = []
        self._previous_active_lanes: set[int] = set()
        self._receptor_feedback_colors: dict[int, tuple[int, int, int]] = {
            lane: (255, 255, 255) for lane in range(GAMEPLAY.lane_count)
        }

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

    def run(self) -> None:
        pygame.init()
        screen = pygame.display.set_mode((WINDOW.width, WINDOW.height))
        pygame.display.set_caption(WINDOW.title)
        clock = pygame.time.Clock()
        self.render_system = self.factory.create_render_system()
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
            self._resolve_pointer_hits(newly_pressed_lanes, current_time, receptors)
            self._handle_open_palm_chords(gestures, current_time, receptors)
            self._resolve_misses(current_time)
            self._previous_active_lanes = active_lanes

            self.render_system.draw_frame(
                screen=screen,
                notes=self.notes,
                receptors=receptors,
                lane_positions=lane_positions,
                score_state=self.score_system.state,
                active_lanes=active_lanes,
                pointer_positions=pointer_positions,
                receptor_feedback_colors=self._receptor_feedback_colors,
                camera_frame=self.hand_adapter.get_frame(),
            )
            pygame.display.flip()

            if current_time > RHYTHM.song_duration_seconds and not self.notes:
                running = False

        self.audio_clock.stop()
        self.hand_adapter.shutdown()
        self.store.save_results(self.score_system.state)
        pygame.quit()

    def _resolve_pointer_hits(self, active_lanes: set[int], current_time: float, receptors: list[LaneReceptor]) -> None:
        catcher_used_this_frame = set(active_lanes)
        catcher_had_tiles_available: set[int] = set()
        catcher_caught_tiles_this_frame: set[int] = set()

        for lane in active_lanes:
            lane_notes = [n for n in self.notes if n.lane == lane and not n.judged]
            if not lane_notes:
                continue
            receptor = receptors[lane]
            catchable = [
                n for n in lane_notes if abs((n.y + GAMEPLAY.note_size / 2) - (receptor.y + receptor.size / 2)) <= 75
            ]
            if catchable:
                catcher_had_tiles_available.add(lane)
                note = min(catchable, key=lambda n: abs(n.scheduled_time - current_time))
                judgement = self.timing_judge.classify(current_time, note.scheduled_time)
                if judgement in {"perfect", "good", "miss"}:
                    note.judged = True
                    note.hit_time = current_time
                    catcher_caught_tiles_this_frame.add(lane)
                    self.score_system.apply_judgement(judgement)

        self.notes = [note for note in self.notes if not note.judged]
        self._apply_feedback(
            catcher_used_this_frame=catcher_used_this_frame,
            catcher_had_tiles_available=catcher_had_tiles_available,
            catcher_caught_tiles_this_frame=catcher_caught_tiles_this_frame,
        )

    def _handle_open_palm_chords(self, gestures: list[str], current_time: float, receptors: list[LaneReceptor]) -> None:
        if "Open_Palm" not in gestures:
            return

        catcher_used_this_frame = set(range(GAMEPLAY.lane_count))
        catcher_had_tiles_available: set[int] = set()
        catcher_caught_tiles_this_frame: set[int] = set()

        for lane in range(GAMEPLAY.lane_count):
            receptor = receptors[lane]
            lane_chords = [
                n
                for n in self.notes
                if n.lane == lane and n.kind == NoteKind.CHORD and not n.judged
                and abs((n.y + GAMEPLAY.note_size / 2) - (receptor.y + receptor.size / 2)) <= 75
            ]
            if lane_chords:
                catcher_had_tiles_available.add(lane)
                note = min(lane_chords, key=lambda n: abs(n.scheduled_time - current_time))
                judgement = self.timing_judge.classify(current_time, note.scheduled_time)
                if judgement in {"perfect", "good", "miss"}:
                    note.judged = True
                    note.hit_time = current_time
                    catcher_caught_tiles_this_frame.add(lane)
                    self.score_system.apply_judgement(judgement)

        self.notes = [note for note in self.notes if not note.judged]
        self._apply_feedback(
            catcher_used_this_frame=catcher_used_this_frame,
            catcher_had_tiles_available=catcher_had_tiles_available,
            catcher_caught_tiles_this_frame=catcher_caught_tiles_this_frame,
        )

    def _resolve_misses(self, current_time: float) -> None:
        remaining: list[Note] = []
        for note in self.notes:
            judgement = self.timing_judge.classify(current_time, note.scheduled_time)
            if judgement == "late":
                self.score_system.apply_judgement("miss")
                continue
            remaining.append(note)
        self.notes = remaining

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
                self.score_system.state.score -= 1
            else:
                self._receptor_feedback_colors[lane] = (255, 255, 255)

