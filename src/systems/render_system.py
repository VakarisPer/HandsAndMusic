"""Pygame rendering system."""

import pygame
import cv2
from src.domain.models import LaneReceptor, Note, ScoreState


class RenderSystem:
    """Handles drawing only; no gameplay decisions."""

    def __init__(self) -> None:
        self.font_small = pygame.font.Font(None, 36)
        self.font_big = pygame.font.Font(None, 48)

    def draw_frame(
        self,
        screen: pygame.Surface,
        notes: list[Note],
        receptors: list[LaneReceptor],
        lane_positions: list[float],
        score_state: ScoreState,
        active_lanes: set[int],
        pointer_positions: list[tuple[float, float]],
        receptor_feedback_colors: dict[int, tuple[int, int, int]],
        camera_frame=None,
    ) -> None:
        if camera_frame is not None:
            frame_resized = cv2.resize(camera_frame, (screen.get_width(), screen.get_height()))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.image.fromstring(
                frame_rgb.tobytes(),
                frame_rgb.shape[1::-1],
                "RGB",
            )
            screen.blit(frame_surface, (0, 0))
        else:
            screen.fill("black")
        lane_top = 0
        lane_bottom = screen.get_height()
        for x in lane_positions:
            pygame.draw.line(screen, (40, 40, 40), (int(x) + 15, lane_top), (int(x) + 15, lane_bottom), 1)

        for note in notes:
            if note.kind.value == "hold":
                note_color = (255, 200, 70)
            elif note.kind.value == "chord":
                note_color = (0, 200, 255)
            else:
                note_color = (230, 230, 230)
            pygame.draw.rect(screen, note_color, (lane_positions[note.lane], note.y, 30, 30))

        for receptor in receptors:
            color = receptor_feedback_colors.get(receptor.lane, (255, 255, 255))
            if receptor.lane in active_lanes and color == (255, 255, 255):
                color = (0, 255, 140)
            pygame.draw.rect(screen, color, (receptor.x, receptor.y, receptor.size, receptor.size), 2)

        for normalized_x, normalized_y in pointer_positions:
            px = int(normalized_x * screen.get_width())
            py = int(normalized_y * screen.get_height())
            pygame.draw.circle(screen, (0, 255, 255), (px, py), 14, 2)
            pygame.draw.line(screen, (0, 255, 255), (px - 18, py), (px + 18, py), 2)
            pygame.draw.line(screen, (0, 255, 255), (px, py - 18), (px, py + 18), 2)

        score_text = self.font_big.render(f"Score: {score_state.score}", True, (255, 255, 255))
        combo_text = self.font_small.render(f"Combo: {score_state.combo}  Max: {score_state.max_combo}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        screen.blit(combo_text, (10, 58))

