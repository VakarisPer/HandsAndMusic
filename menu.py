"""Pre-game menu — camera feed + two hand-clickable buttons."""

import pygame

from GameLoop import display_user_camera, draw_finger_indicators, \
    _screen_pos_from_finger
from config import GameConfig


class Button:
    """Rectangular button activated by a pointer-finger click.

    Uses a one-shot 'armed' flag — a finger that lingers inside doesn't
    re-trigger the button until it leaves the rectangle.
    """

    def __init__(self, label, rect, color):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.color = color
        self.armed = True

    def contains(self, point):
        if point is None:
            return False
        return self.rect.collidepoint(point[0], point[1])

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=12)
        pygame.draw.rect(screen, GameConfig.COLOR_WHITE, self.rect,
                         width=3, border_radius=12)
        text = font.render(self.label, True, GameConfig.COLOR_WHITE)
        screen.blit(text, text.get_rect(center=self.rect.center))


def run_menu(screen, tracker, config):
    """Show menu until a button is clicked or the window is closed.

    Returns "start", "exit", or "exit" on window close.
    """
    clock = pygame.time.Clock()
    font_btn = pygame.font.Font(None, 64)
    font_title = pygame.font.Font(None, 72)

    cx = screen.get_width() // 2
    cy = screen.get_height() // 2
    btn_w, btn_h, gap = 320, 110, 30

    start_btn = Button("START",
                       (cx - btn_w // 2, cy - btn_h - gap // 2,
                        btn_w, btn_h),
                       (0, 140, 0))
    exit_btn = Button("EXIT",
                      (cx - btn_w // 2, cy + gap // 2, btn_w, btn_h),
                      (160, 0, 0))
    buttons = (start_btn, exit_btn)
    actions = {start_btn: "start", exit_btn: "exit"}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"

        screen.fill(config.COLOR_BLACK)
        display_user_camera(screen, tracker)

        if not tracker.process_frame():
            clock.tick(config.SCREEN_FPS)
            continue

        hand0_pos = _screen_pos_from_finger(
            tracker.get_finger_position(0, finger_index=8), screen)
        hand1_pos = _screen_pos_from_finger(
            tracker.get_finger_position(1, finger_index=8), screen)
        finger_positions = [p for p in (hand0_pos, hand1_pos)
                            if p is not None]

        title = font_title.render("Hand Gesture Rhythm Game",
                                  True, GameConfig.COLOR_WHITE)
        screen.blit(title, title.get_rect(center=(cx, 80)))

        for btn in buttons:
            inside = any(btn.contains(p) for p in finger_positions)
            if inside and btn.armed:
                btn.armed = False
                draw_finger_indicators(screen, hand0_pos, hand1_pos)
                pygame.display.flip()
                return actions[btn]
            if not inside:
                btn.armed = True
            btn.draw(screen, font_btn)

        draw_finger_indicators(screen, hand0_pos, hand1_pos)
        pygame.display.flip()
        clock.tick(config.SCREEN_FPS)
