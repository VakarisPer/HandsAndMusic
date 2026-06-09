import os
import tkinter as tk
from tkinter import filedialog

import pygame

from GameLoop import display_user_camera, draw_finger_indicators, \
    to_screen_coordinates
from config import GameConfig


def _pick_audio_file():
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()
        filepath = filedialog.askopenfilename(
            parent=root,
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("All Files", "*.*"),
            ],
        )
        root.destroy()
        return str(filepath) if filepath else None
    except Exception as e:
        print(f"[Menu] File dialog failed: {e}")
        return None


class Slider:
    def __init__(self, rect, min_val, max_val, start_val):
        self.rect = pygame.Rect(rect)
        self.min = min_val
        self.max = max_val
        self.value = start_val
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.width))
            self.value = self.min + (rel_x / self.rect.width) * (self.max - self.min)

    def draw(self, screen, config):
        track = self.rect.inflate(0, -self.rect.height * 0.6)
        track.centery = self.rect.centery
        pygame.draw.rect(screen, config.UI_SLIDER_TRACK, track,
                         border_radius=track.height // 2)

        ratio = (self.value - self.min) / (self.max - self.min)
        fill_w = int(track.width * ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(track.x, track.y, fill_w, track.height)
            pygame.draw.rect(screen, config.UI_SLIDER_FILL, fill_rect,
                             border_radius=track.height // 2)

        knob_x = track.x + fill_w
        knob_y = track.centery
        pygame.draw.circle(screen, config.UI_SLIDER_KNOB, (knob_x, knob_y), 12)
        pygame.draw.circle(screen, config.UI_ACCENT, (knob_x, knob_y), 12, 2)


class Button:
    def __init__(self, label, rect, color, font_size=40):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.color = color
        self.font = pygame.font.Font(GameConfig.FONT_PATH, font_size)
        self.armed = True
        self.hovered = False
        self._pulse = 0.0
        self._done_click = False

    def contains(self, point):
        return self.rect.collidepoint(point[0], point[1])

    def update(self, hovered, delta_time):
        self.hovered = hovered
        if hovered:
            self._pulse = min(1.0, self._pulse + delta_time * 5)
        else:
            self._pulse = max(0.0, self._pulse - delta_time * 5)

    def draw(self, screen):
        r, g, b = self.color
        if self.hovered:
            r = min(255, r + 55)
            g = min(255, g + 55)
            b = min(255, b + 55)

        sh = self.rect.copy()
        sh.y += 3
        pygame.draw.rect(screen, (0, 0, 0, 80), sh, border_radius=14)

        pygame.draw.rect(screen, (r, g, b), self.rect, border_radius=14)
        pygame.draw.rect(screen, (255, 255, 255, 70), self.rect,
                         width=2, border_radius=14)

        g = int(20 * self._pulse)
        if g > 0:
            glow = pygame.Surface(
                (self.rect.width + g * 2, self.rect.height + g * 2),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(glow, (*self.color, 35),
                             glow.get_rect(), border_radius=16)
            screen.blit(glow, (self.rect.x - g, self.rect.y - g))

        text = self.font.render(self.label, True,
                                GameConfig.UI_TEXT_PRIMARY)
        screen.blit(text, text.get_rect(center=self.rect.center))


class MenuButton(Button):
    def __init__(self, label, rect, color):
        super().__init__(label, rect, color, font_size=28)

    def point_inside(self, screen_pos):
        if screen_pos is None:
            return False
        return self.rect.collidepoint(screen_pos[0], screen_pos[1])


def _draw_panel(screen, rect, color):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill(color)
    screen.blit(panel, rect)


def run_settings(screen, config):
    clock = pygame.time.Clock()
    font_large = pygame.font.Font(config.FONT_PATH, 32)
    font_medium = pygame.font.Font(config.FONT_PATH, 24)
    font_small = pygame.font.Font(config.FONT_PATH, 18)

    sw, sh = screen.get_width(), screen.get_height()
    pw, ph = 620, 450
    px = (sw - pw) // 2
    py = (sh - ph) // 2

    slider = Slider((px + 80, py + 170, pw - 160, 30),
                    min_val=0.0, max_val=1.0, start_val=config.MUSIC_VOLUME)

    back_btn = Button("BACK",
                      (px + pw // 2 - 140, py + ph - 80, 280, 56),
                      config.UI_BUTTON_EXIT, font_size=22)

    browse_btn = Button("BROWSE...",
                        (px + pw - 200, py + 120, 120, 42),
                        config.UI_ACCENT, font_size=18)

    current_file = config.AUDIO_FILE
    status_message = ""
    status_timer = 0.0

    while True:
        delta_time = clock.tick(config.SCREEN_FPS) / 1000
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit", config
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back", config
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            slider.handle_event(event)

        screen.fill(config.COLOR_BLACK)

        # We still show camera but black means camera isn't shown during settings
        # since there's no tracker. Let's just use the panel without camera.
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((8, 8, 24, 255))
        screen.blit(overlay, (0, 0))

        _draw_panel(screen, pygame.Rect(px, py, pw, ph), config.UI_PANEL)

        title = font_large.render("Settings", True, config.UI_TEXT_PRIMARY)
        screen.blit(title, title.get_rect(center=(sw // 2, py + 40)))

        vol_label = font_medium.render(f"Volume: {int(slider.value * 100)}%",
                                       True, config.UI_TEXT_SECONDARY)
        screen.blit(vol_label, (px + 80, py + 120))

        slider.draw(screen, config)

        file_label = font_small.render("Current Track:", True,
                                       config.UI_TEXT_SECONDARY)
        screen.blit(file_label, (px + 60, py + 230))
        short_name = os.path.basename(current_file) if current_file else "None"
        file_text = font_small.render(short_name, True,
                                      config.UI_TEXT_PRIMARY)
        screen.blit(file_text, (px + 60, py + 256))

        if status_timer > 0:
            status_timer -= delta_time
            clr = config.COLOR_GREEN if "success" not in status_message.lower() \
                and "selected" not in status_message.lower() \
                or "selected" in status_message.lower() \
                else config.COLOR_GREEN
            status = font_small.render(status_message, True, config.COLOR_GREEN)
            screen.blit(status, status.get_rect(
                center=(sw // 2, py + 310)))

        hover_back = back_btn.rect.collidepoint(mouse_pos)
        hover_browse = browse_btn.rect.collidepoint(mouse_pos)
        back_btn.update(hover_back, delta_time)
        browse_btn.update(hover_browse, delta_time)
        back_btn.draw(screen)
        browse_btn.draw(screen)

        if mouse_clicked:
            if back_btn.rect.collidepoint(mouse_pos):
                config.MUSIC_VOLUME = slider.value
                return "back", config
            if browse_btn.rect.collidepoint(mouse_pos):
                pygame.display.flip()
                picked = _pick_audio_file()
                if picked and os.path.exists(picked):
                    if picked != current_file:
                        current_file = picked
                        config.AUDIO_FILE = picked
                        status_message = "Track selected!"
                        status_timer = 3.0
                    else:
                        status_message = "Already selected."
                        status_timer = 2.0
                elif picked:
                    status_message = "File not found."
                    status_timer = 2.0

        config.MUSIC_VOLUME = slider.value

        pygame.display.flip()


def run_menu(screen, tracker, config):
    clock = pygame.time.Clock()
    font_title = pygame.font.Font(config.FONT_PATH, 40)
    font_sub = pygame.font.Font(config.FONT_PATH, 16)
    font_msg = pygame.font.Font(config.FONT_PATH, 18)

    cx = screen.get_width() // 2
    cy = screen.get_height() // 2 + 20
    bw, bh, gap = 320, 90, 22

    start_btn = MenuButton("START",
                           (cx - bw // 2, cy - bh * 2 - gap,
                            bw, bh),
                           config.UI_BUTTON_START)
    settings_btn = MenuButton("SETTINGS",
                              (cx - bw // 2, cy - bh // 2,
                               bw, bh),
                              config.UI_BUTTON_SETTINGS)
    exit_btn = MenuButton("EXIT",
                          (cx - bw // 2, cy + bh + gap, bw, bh),
                          config.UI_BUTTON_EXIT)

    menu_buttons = (start_btn, settings_btn, exit_btn)
    actions = {start_btn: "start", settings_btn: "settings", exit_btn: "exit"}

    status_text = ""
    status_timer = 0.0

    while True:
        delta_time = clock.tick(config.SCREEN_FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"

        screen.fill(config.COLOR_BLACK)
        display_user_camera(screen, tracker)

        overlay = pygame.Surface((screen.get_width(), screen.get_height()),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        title = font_title.render("RhythmForge", True, config.UI_TEXT_PRIMARY)
        screen.blit(title, title.get_rect(center=(cx, 55)))
        subtitle = font_sub.render("Hand Gesture Rhythm Game", True,
                                   config.UI_TEXT_SECONDARY)
        screen.blit(subtitle, subtitle.get_rect(center=(cx, 105)))

        track_name = os.path.basename(config.AUDIO_FILE) if config.AUDIO_FILE \
            else "No track selected"
        track_color = config.UI_TEXT_SECONDARY if config.AUDIO_FILE \
            else config.UI_TEXT_WARN
        track_info = font_sub.render(f"Track: {track_name}", True, track_color)
        screen.blit(track_info, track_info.get_rect(center=(cx, 133)))

        if status_timer > 0:
            status_timer -= delta_time
            msg = font_msg.render(status_text, True, config.UI_TEXT_WARN)
            screen.blit(msg, msg.get_rect(center=(cx, cy + bh * 2 + 20)))

        if not tracker.process_frame():
            for btn in menu_buttons:
                btn.update(False, delta_time)
                btn.draw(screen)
            pygame.display.flip()
            continue

        hand0_pos = to_screen_coordinates(
            tracker.get_finger_position(0, finger_index=8), screen)
        hand1_pos = to_screen_coordinates(
            tracker.get_finger_position(1, finger_index=8), screen)
        finger_positions = [p for p in (hand0_pos, hand1_pos)
                            if p is not None]

        for btn in menu_buttons:
            hovered = any(btn.point_inside(p) for p in finger_positions)
            btn.update(hovered, delta_time)
            btn.draw(screen)

            inside = any(btn.point_inside(p) for p in finger_positions)
            if inside and btn.armed:
                btn.armed = False
                action = actions[btn]
                draw_finger_indicators(screen, hand0_pos, hand1_pos)
                pygame.display.flip()

                if action == "settings":
                    result, config = run_settings(screen, config)
                    if result == "exit":
                        return "exit"
                elif action == "start":
                    if not config.AUDIO_FILE or not os.path.exists(config.AUDIO_FILE):
                        status_text = "Select a track in Settings first!"
                        status_timer = 2.0
                        btn.armed = True
                    else:
                        return action
                else:
                    return action
            if not inside:
                btn.armed = True

        draw_finger_indicators(screen, hand0_pos, hand1_pos)
        pygame.display.flip()
