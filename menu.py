import os
import math
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
        self.enabled = True

    def contains(self, point):
        return self.rect.collidepoint(point[0], point[1])

    def update(self, hovered, delta_time):
        if not self.enabled:
            self.hovered = False
            self._pulse = max(0.0, self._pulse - delta_time * 5)
            return
        self.hovered = hovered
        if hovered:
            self._pulse = min(1.0, self._pulse + delta_time * 5)
        else:
            self._pulse = max(0.0, self._pulse - delta_time * 5)

    def draw(self, screen):
        if self.enabled:
            r, g, b = self.color
            if self.hovered:
                r = min(255, r + 55)
                g = min(255, g + 55)
                b = min(255, b + 55)
        else:
            r, g, b = GameConfig.UI_BUTTON_DISABLED

        sh = self.rect.copy()
        sh.y += 3
        pygame.draw.rect(screen, (0, 0, 0, 80), sh, border_radius=14)

        pygame.draw.rect(screen, (r, g, b), self.rect, border_radius=14)
        pygame.draw.rect(screen, (255, 255, 255, 40 if not self.enabled else 70),
                         self.rect, width=2, border_radius=14)

        if self.enabled:
            g = int(20 * self._pulse)
            if g > 0:
                glow = pygame.Surface(
                    (self.rect.width + g * 2, self.rect.height + g * 2),
                    pygame.SRCALPHA,
                )
                pygame.draw.rect(glow, (*self.color, 35),
                                 glow.get_rect(), border_radius=16)
                screen.blit(glow, (self.rect.x - g, self.rect.y - g))

        text_color = GameConfig.UI_TEXT_PRIMARY if self.enabled \
            else (120, 120, 130)
        text = self.font.render(self.label, True, text_color)
        screen.blit(text, text.get_rect(center=self.rect.center))


class MenuButton(Button):
    def __init__(self, label, rect, color):
        super().__init__(label, rect, color, font_size=28)

    def point_inside(self, screen_pos):
        if screen_pos is None or not self.enabled:
            return False
        return self.rect.collidepoint(screen_pos[0], screen_pos[1])


class TextInput:
    def __init__(self, rect, placeholder="Enter name...", max_length=15):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.max_length = max_length
        self.text = ""
        self.focused = False
        self._cursor_visible = True
        self._cursor_timer = 0.0
        self._pulse = 0.0
        self.font = pygame.font.Font(GameConfig.FONT_PATH, 26)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.focused = False
            elif event.key == pygame.K_ESCAPE:
                self.focused = False
            elif len(self.text) < self.max_length:
                char = event.unicode
                if char.isprintable():
                    self.text += char

    def update(self, delta_time):
        self._cursor_timer += delta_time
        if self._cursor_timer > 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

        if self.focused:
            self._pulse = min(1.0, self._pulse + delta_time * 5)
        else:
            self._pulse = max(0.0, self._pulse - delta_time * 5)

    def draw(self, screen, config):
        border_color = config.USERNAME_INPUT_FOCUS_BORDER if self.focused \
            else config.USERNAME_INPUT_BORDER

        r, g, b = border_color
        glow = int(8 * self._pulse)
        if glow > 0:
            glow_surf = pygame.Surface(
                (self.rect.width + glow * 2, self.rect.height + glow * 2),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(glow_surf, (r, g, b, 40),
                             glow_surf.get_rect(), border_radius=12)
            screen.blit(glow_surf, (self.rect.x - glow, self.rect.y - glow))

        pygame.draw.rect(screen, config.USERNAME_INPUT_BG, self.rect,
                         border_radius=10)
        pygame.draw.rect(screen, border_color, self.rect, width=2,
                         border_radius=10)

        if self.text:
            text_color = config.USERNAME_INPUT_TEXT
            txt = self.font.render(self.text, True, text_color)
        else:
            text_color = config.USERNAME_INPUT_PLACEHOLDER
            txt = self.font.render(self.placeholder, True, text_color)

        txt_rect = txt.get_rect(
            midleft=(self.rect.x + 15, self.rect.centery))
        screen.blit(txt, txt_rect)

        if self.focused and self._cursor_visible:
            if self.text:
                cursor_x = txt_rect.right + 4
            else:
                cursor_x = txt_rect.left
            cursor_y_top = self.rect.centery - 12
            cursor_y_bot = self.rect.centery + 12
            pygame.draw.line(screen, config.USERNAME_INPUT_CURSOR,
                             (cursor_x, cursor_y_top),
                             (cursor_x, cursor_y_bot), 2)


def _draw_leaderboard(screen, config, score_manager):
    panel_w, panel_h = 340, 500
    panel_x = 20
    panel_y = (screen.get_height() - panel_h) // 2

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel_surf.fill(config.LEADERBOARD_BG)
    screen.blit(panel_surf, (panel_x, panel_y))
    pygame.draw.rect(screen, config.LEADERBOARD_BORDER,
                     (panel_x, panel_y, panel_w, panel_h), width=2,
                     border_radius=10)

    header_font = pygame.font.Font(config.FONT_PATH, 18)
    header = header_font.render("LEADERBOARD", True,
                                config.UI_ACCENT)
    header_rect = header.get_rect(center=(panel_x + panel_w // 2, panel_y + 22))
    screen.blit(header, header_rect)

    divider_y = panel_y + 42
    pygame.draw.line(screen, config.LEADERBOARD_BORDER,
                     (panel_x + 16, divider_y),
                     (panel_x + panel_w - 16, divider_y), 1)

    col_font = pygame.font.Font(config.FONT_PATH, 11)
    col_y = panel_y + 49
    for col_text, col_x in [("#", panel_x + 20),
                             ("NAME", panel_x + 52),
                             ("SCORE", panel_x + 168),
                             ("COMBO", panel_x + 258)]:
        lbl = col_font.render(col_text, True, config.UI_TEXT_SECONDARY)
        screen.blit(lbl, (col_x, col_y))

    row_start_y = panel_y + 66
    row_h = 36
    max_rows = 10
    entry_font = pygame.font.Font(config.FONT_PATH, 13)
    rank_font = pygame.font.Font(config.FONT_PATH, 14)

    scores = score_manager.get_high_scores(max_rows)

    if not scores:
        empty = entry_font.render("No scores yet!", True,
                                  config.UI_TEXT_SECONDARY)
        screen.blit(empty, (panel_x + panel_w // 2 - empty.get_width() // 2,
                            row_start_y + 40))
        return

    for i, entry in enumerate(scores):
        row_y = row_start_y + i * row_h

        rank = i + 1
        if rank == 1:
            bg_color = config.LEADERBOARD_GOLD_BG
            rank_color = config.LEADERBOARD_GOLD
        elif rank == 2:
            bg_color = config.LEADERBOARD_SILVER_BG
            rank_color = config.LEADERBOARD_SILVER
        elif rank == 3:
            bg_color = config.LEADERBOARD_BRONZE_BG
            rank_color = config.LEADERBOARD_BRONZE
        else:
            bg_color = config.LEADERBOARD_ROW_ALT if i % 2 == 0 \
                else config.LEADERBOARD_ROW_BG
            rank_color = config.UI_TEXT_SECONDARY

        row_surf = pygame.Surface((panel_w - 4, row_h), pygame.SRCALPHA)
        row_surf.fill(bg_color)
        screen.blit(row_surf, (panel_x + 2, row_y))

        rank_text = rank_font.render(str(rank), True, rank_color)
        screen.blit(rank_text, (panel_x + 20, row_y + row_h // 2
                                - rank_text.get_height() // 2))

        name = entry.get("player", "???")[:10]
        name_text = entry_font.render(name, True, config.UI_TEXT_PRIMARY)
        screen.blit(name_text, (panel_x + 52, row_y + row_h // 2
                                - name_text.get_height() // 2))

        score_text = entry_font.render(str(entry.get("score", 0)), True,
                                       config.UI_TEXT_PRIMARY)
        screen.blit(score_text, (panel_x + 168, row_y + row_h // 2
                                 - score_text.get_height() // 2))

        combo_text = entry_font.render(str(entry.get("max_combo", 0)), True,
                                       config.SCORE_DISPLAY_COMBO)
        screen.blit(combo_text, (panel_x + 258, row_y + row_h // 2
                                 - combo_text.get_height() // 2))


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
    pw, ph = 620, 530
    px = (sw - pw) // 2
    py = (sh - ph) // 2

    slider = Slider((px + 80, py + 140, pw - 160, 30),
                    min_val=0.0, max_val=1.0, start_val=config.MUSIC_VOLUME)

    name_input = TextInput(
        (px + 80, py + 225, pw - 160, 42),
        placeholder="Enter your name..."
    )
    name_input.text = config.USERNAME

    back_btn = Button("BACK",
                      (px + pw // 2 - 140, py + ph - 80, 280, 56),
                      config.UI_BUTTON_EXIT, font_size=22)

    browse_btn = Button("BROWSE...",
                        (px + pw - 200, py + 300, 120, 42),
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
                if event.key == pygame.K_ESCAPE and not name_input.focused:
                    return "back", config
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            slider.handle_event(event)
            name_input.handle_event(event)

        screen.fill(config.COLOR_BLACK)

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((8, 8, 24, 255))
        screen.blit(overlay, (0, 0))

        _draw_panel(screen, pygame.Rect(px, py, pw, ph), config.UI_PANEL)

        title = font_large.render("Settings", True, config.UI_TEXT_PRIMARY)
        screen.blit(title, title.get_rect(center=(sw // 2, py + 40)))

        vol_label = font_medium.render(f"Volume: {int(slider.value * 100)}%",
                                       True, config.UI_TEXT_SECONDARY)
        screen.blit(vol_label, (px + 80, py + 100))

        slider.draw(screen, config)

        name_label = font_medium.render("Your Name", True,
                                        config.UI_TEXT_SECONDARY)
        screen.blit(name_label, (px + 80, py + 195))

        name_input.focused = name_input.focused or \
            name_input.rect.collidepoint(mouse_pos)
        name_input.update(delta_time)
        name_input.draw(screen, config)

        file_label = font_small.render("Current Track:", True,
                                       config.UI_TEXT_SECONDARY)
        screen.blit(file_label, (px + 60, py + 310))
        short_name = os.path.basename(current_file) if current_file else "None"
        file_text = font_small.render(short_name, True,
                                      config.UI_TEXT_PRIMARY)
        screen.blit(file_text, (px + 60, py + 336))

        if status_timer > 0:
            status_timer -= delta_time
            status = font_small.render(status_message, True,
                                       config.COLOR_GREEN)
            screen.blit(status, status.get_rect(
                center=(sw // 2, py + 390)))

        hover_back = back_btn.rect.collidepoint(mouse_pos)
        hover_browse = browse_btn.rect.collidepoint(mouse_pos)
        back_btn.update(hover_back, delta_time)
        browse_btn.update(hover_browse, delta_time)
        back_btn.draw(screen)
        browse_btn.draw(screen)

        if mouse_clicked:
            if back_btn.rect.collidepoint(mouse_pos):
                config.MUSIC_VOLUME = slider.value
                config.USERNAME = name_input.text.strip()
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
        config.USERNAME = name_input.text.strip()

        pygame.display.flip()


def run_menu(screen, config, score_manager):
    clock = pygame.time.Clock()
    font_title = pygame.font.Font(config.FONT_PATH, 48)
    font_sub = pygame.font.Font(config.FONT_PATH, 16)
    font_msg = pygame.font.Font(config.FONT_PATH, 18)

    cx = screen.get_width() // 2
    cy = screen.get_height() // 2 + 20
    bw, bh, gap = 320, 76, 18

    start_btn = MenuButton("START",
                           (cx - bw // 2, cy - 40,
                            bw, bh),
                           config.UI_BUTTON_START)
    settings_btn = MenuButton("SETTINGS",
                              (cx - bw // 2, cy + bh - 40 + gap,
                               bw, bh),
                              config.UI_BUTTON_SETTINGS)
    exit_btn = MenuButton("EXIT",
                          (cx - bw // 2, cy + (bh + gap) * 2 - 40, bw, bh),
                          config.UI_BUTTON_EXIT)

    menu_buttons = (start_btn, settings_btn, exit_btn)
    actions = {start_btn: "start", settings_btn: "settings",
               exit_btn: "exit"}

    status_text = ""
    status_timer = 0.0
    title_anim = 0.0

    while True:
        delta_time = clock.tick(config.SCREEN_FPS) / 1000
        title_anim += delta_time

        has_name = bool(config.USERNAME.strip())
        has_music = bool(config.AUDIO_FILE) and os.path.exists(config.AUDIO_FILE)
        start_btn.enabled = has_name and has_music

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "", "exit"

        screen.fill(config.COLOR_BLACK)
        display_user_camera(screen)

        overlay = pygame.Surface((screen.get_width(), screen.get_height()),
                                 pygame.SRCALPHA)
        overlay.fill((4, 4, 18, 160))
        screen.blit(overlay, (0, 0))

        _draw_leaderboard(screen, config, score_manager)

        title_color = config.rainbow_color(title_anim * 1.5, 1.0, 1.0)
        title = font_title.render("Hands & Music", True, title_color)
        title_rect = title.get_rect(center=(cx, 55))
        for i in range(5, 0, -1):
            alpha = 15 // i
            scaled = pygame.transform.scale(
                title, (title.get_width() + i * 8,
                        title.get_height() + i * 4))
            scaled.set_alpha(alpha)
            scaled_rect = scaled.get_rect(center=title_rect.center)
            screen.blit(scaled, scaled_rect)
        screen.blit(title, title_rect)

        subtitle = font_sub.render("Hand Gesture Rhythm Game", True,
                                   config.UI_TEXT_SECONDARY)
        screen.blit(subtitle, subtitle.get_rect(center=(cx, 105)))

        track_name = os.path.basename(config.AUDIO_FILE) if config.AUDIO_FILE \
            else "Not set"
        track_color = config.UI_TEXT_SECONDARY if config.AUDIO_FILE \
            else config.UI_TEXT_WARN
        track_info = font_sub.render(f"Track: {track_name}", True, track_color)
        screen.blit(track_info, track_info.get_rect(center=(cx, 133)))

        name_display = config.USERNAME if has_name else "Not set"
        name_color = config.UI_TEXT_SECONDARY if has_name \
            else config.UI_TEXT_WARN
        name_info = font_sub.render(f"Player: {name_display}", True, name_color)
        screen.blit(name_info, name_info.get_rect(center=(cx, 160)))

        if not start_btn.enabled:
            msgs = []
            if not has_name:
                msgs.append("Set name in Settings")
            if not has_music:
                msgs.append("Select a track in Settings")
            warn = font_msg.render(" | ".join(msgs), True,
                                   config.UI_TEXT_WARN)
            screen.blit(warn, warn.get_rect(center=(cx, start_btn.rect.top - 20)))

        if status_timer > 0:
            status_timer -= delta_time
            msg = font_msg.render(status_text, True, config.UI_TEXT_WARN)
            screen.blit(msg, msg.get_rect(
                center=(cx, exit_btn.rect.bottom + 30)))

        if not hasattr(display_user_camera, 'tracker') or \
                not display_user_camera.tracker:
            for btn in menu_buttons:
                btn.update(False, delta_time)
                btn.draw(screen)
            pygame.display.flip()
            continue

        hand0_pos = to_screen_coordinates(
            display_user_camera.tracker.get_finger_position(0,
                                                            finger_index=8),
            screen)
        hand1_pos = to_screen_coordinates(
            display_user_camera.tracker.get_finger_position(1,
                                                            finger_index=8),
            screen)
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
                        return "", "exit"
                elif action == "start":
                    if not config.AUDIO_FILE or \
                            not os.path.exists(config.AUDIO_FILE):
                        status_text = "Select a track in Settings first!"
                        status_timer = 2.0
                        btn.armed = True
                    elif not config.USERNAME.strip():
                        status_text = "Set your name in Settings first!"
                        status_timer = 2.0
                        btn.armed = True
                    else:
                        return config.USERNAME.strip(), action
                else:
                    return "", action
            if not inside:
                btn.armed = True

        draw_finger_indicators(screen, hand0_pos, hand1_pos)
        pygame.display.flip()
