import math
import time

import pygame
import cv2

from pathlib import Path
from src.domain.models import LaneReceptor, Note, ScoreState


class BouncingNumber:
    def __init__(self):
        self.value = 0
        self.bounce = 0.0

    def set(self, new_value):
        if new_value != self.value:
            self.bounce = min(1.5, self.bounce + 0.7)
        self.value = new_value

    def update(self, delta_time):
        self.bounce = max(0.0, self.bounce - delta_time * 3.5)

    def scale(self):
        return 1.0 + self.bounce * 0.5

    def color_tint(self, base_color):
        if self.bounce < 0.1:
            return base_color
        r, g, b = base_color
        factor = self.bounce / 1.5
        return (
            min(255, r + int(80 * factor)),
            min(255, g + int(40 * factor)),
            b,
        )


def _rainbow_color(t, brightness=0.9):
    r = int((math.sin(t) * 0.5 + 0.5) * 255 * brightness)
    g = int((math.sin(t + 2.094) * 0.5 + 0.5) * 255 * brightness)
    b = int((math.sin(t + 4.189) * 0.5 + 0.5) * 255 * brightness)
    return (r, g, b)


_FONT_PATH = str(Path(__file__).parent.parent.parent / "fonts" / "RobotikaPixelGreek-nAWJR.otf")


class RenderSystem:
    def __init__(self):
        self.font_score = pygame.font.Font(_FONT_PATH, 32)
        self.font_combo = pygame.font.Font(_FONT_PATH, 36)
        self.font_max_combo = pygame.font.Font(_FONT_PATH, 22)
        self._score_anim = BouncingNumber()
        self._combo_anim = BouncingNumber()
        self._camera_surface = None
        self.particle_system = None

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
        delta_time=0.016,
    ) -> None:
        sw, sh = screen.get_width(), screen.get_height()

        if camera_frame is not None:
            if (self._camera_surface is None
                    or self._camera_surface.get_width() != sw
                    or self._camera_surface.get_height() != sh):
                self._camera_surface = pygame.Surface((sw, sh)).convert()
            frame_small = cv2.resize(camera_frame, (sw, sh))
            frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
            pygame.surfarray.blit_array(self._camera_surface,
                                        frame_rgb.swapaxes(0, 1))
            screen.blit(self._camera_surface, (0, 0))
        else:
            screen.fill((8, 8, 18))

        for x in lane_positions:
            pygame.draw.line(screen, (35, 35, 55), (int(x) + 15, 0),
                             (int(x) + 15, sh), 1)

        for note in notes:
            nx, ny = lane_positions[note.lane], note.y

            if hasattr(note, 'is_golden') and note.is_golden:
                pulse = (math.sin(time.time() * 6) + 1) / 2
                alpha = int(60 + pulse * 60)
                glow_sz = 44
                glow_rect = (nx - 7, ny - 7, glow_sz, glow_sz)
                glow_surf = pygame.Surface((glow_sz, glow_sz), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 240, 100, alpha),
                                 glow_surf.get_rect(), border_radius=6)
                screen.blit(glow_surf, glow_rect)
                note_color = (255, 215, 0)
            elif note.kind.value == "hold":
                note_color = (255, 200, 70)
            elif note.kind.value == "chord":
                note_color = (180, 100, 255)
            else:
                note_color = (230, 230, 230)

            rect = (nx, ny, 30, 30)
            pygame.draw.rect(screen, note_color, rect)
            lighter = tuple(min(255, c + 50) for c in note_color)
            pygame.draw.rect(screen, lighter, rect, 2)

        for receptor in receptors:
            rx, ry = receptor.x, receptor.y
            rsz = receptor.size
            color = receptor_feedback_colors.get(receptor.lane, (255, 255, 255))

            if color != (255, 255, 255):
                glow_radius = int(rsz * 0.7)
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2),
                                           pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, 70),
                                   (glow_radius, glow_radius), glow_radius)
                screen.blit(glow_surf, (int(rx + rsz / 2 - glow_radius),
                                        int(ry + rsz / 2 - glow_radius)))
            elif receptor.lane in active_lanes:
                color = (0, 255, 140)

            pygame.draw.rect(screen, color, (rx, ry, rsz, rsz),
                             border_radius=4)
            pygame.draw.rect(screen, (255, 255, 255, 80), (rx, ry, rsz, rsz),
                             2, border_radius=4)

        for normalized_x, normalized_y in pointer_positions:
            px = int(normalized_x * sw)
            py = int(normalized_y * sh)
            glow = pygame.Surface((42, 42), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 255, 255, 50), (21, 21), 20)
            screen.blit(glow, (px - 21, py - 21))
            pygame.draw.circle(screen, (0, 255, 255), (px, py), 14, 2)
            pygame.draw.line(screen, (0, 255, 255), (px - 18, py),
                             (px + 18, py), 2)
            pygame.draw.line(screen, (0, 255, 255), (px, py - 18),
                             (px, py + 18), 2)

        if self.particle_system is not None:
            self.particle_system.update_and_draw(screen, delta_time)

        self._draw_hud(screen, score_state)

    def _draw_hud(self, screen, score_state):
        self._score_anim.set(score_state.score)
        self._combo_anim.set(score_state.combo)
        self._score_anim.update(0.016)
        self._combo_anim.update(0.016)

        score_color = self._score_anim.color_tint((255, 255, 255))
        score_scale = self._score_anim.scale()
        score_surf = self.font_score.render(f"Score: {score_state.score}",
                                            True, score_color)
        if score_scale != 1.0:
            w, h = score_surf.get_size()
            score_surf = pygame.transform.smoothscale(
                score_surf, (int(w * score_scale), int(h * score_scale)))
        screen.blit(score_surf, (20, 20))

        if score_state.combo > 1:
            combo_color = _rainbow_color(time.time() * 2)
            combo_scale = self._combo_anim.scale()
            combo_surf = self.font_combo.render(
                f"x{score_state.combo}", True, combo_color)
            if combo_scale > 1.0:
                w, h = combo_surf.get_size()
                combo_surf = pygame.transform.smoothscale(
                    combo_surf, (int(w * combo_scale), int(h * combo_scale)))
            glow = int(40 * (combo_scale - 1.0))
            if glow > 0:
                gw, gh = combo_surf.get_size()
                glow_surf = pygame.Surface((gw + glow * 2, gh + glow * 2),
                                           pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*combo_color, 30),
                                 glow_surf.get_rect(), border_radius=8)
                screen.blit(glow_surf, (20 - glow, 70 - glow))
            screen.blit(combo_surf, (20, 70))

        if score_state.max_combo > 0:
            mc_surf = self.font_max_combo.render(
                f"Max Combo: {score_state.max_combo}", True, (255, 160, 30))
            screen.blit(mc_surf, (20, 110))
