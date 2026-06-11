import json
import os
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import pygame

from src.ui.camera_overlay import (display_user_camera,
                                     draw_finger_indicators,
                                     release_camera_tracker,
                                     to_screen_coordinates)
from src.config.settings import GameConfig

LEVELS_DIR = Path("levels")


# ---------------------------------------------------------------------------
# File dialog helpers
# ---------------------------------------------------------------------------

def _pick_audio_file():
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()
        path = filedialog.askopenfilename(
            parent=root,
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("All Files", "*.*"),
            ],
        )
        root.destroy()
        return str(path) if path else None
    except Exception as e:
        print(f"[Menu] File dialog failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Level persistence
# ---------------------------------------------------------------------------

def _list_levels() -> list[str]:
    LEVELS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        [p.stem for p in LEVELS_DIR.glob("*.json")],
        key=lambda x: x.lower(),
    )


def _save_level(name: str, audio_file: str, notes: list[dict]) -> Path:
    LEVELS_DIR.mkdir(parents=True, exist_ok=True)
    path = LEVELS_DIR / f"{name}.json"
    # Store the audio path relative to the project root when possible so
    # levels keep working if the project folder is moved or shared.
    try:
        audio_file = str(Path(audio_file).resolve().relative_to(Path.cwd()))
    except ValueError:
        pass
    payload = {
        "name": name,
        "audio_file": audio_file,
        "notes": notes,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

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
        self.enabled = True

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
        border_alpha = 40 if not self.enabled else 70
        pygame.draw.rect(screen, (255, 255, 255, border_alpha), self.rect,
                         width=2, border_radius=14)

        if self.enabled:
            g = int(20 * self._pulse)
            if g > 0:
                glow = pygame.Surface(
                    (self.rect.width + g * 2, self.rect.height + g * 2),
                    pygame.SRCALPHA)
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
    def __init__(self, rect, placeholder="Enter text...", max_length=20):
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
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
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
                pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (r, g, b, 40),
                             glow_surf.get_rect(), border_radius=12)
            screen.blit(glow_surf, (self.rect.x - glow, self.rect.y - glow))
        pygame.draw.rect(screen, config.USERNAME_INPUT_BG, self.rect,
                         border_radius=10)
        pygame.draw.rect(screen, border_color, self.rect, width=2,
                         border_radius=10)
        if self.text:
            txt = self.font.render(self.text, True, config.USERNAME_INPUT_TEXT)
        else:
            txt = self.font.render(self.placeholder, True,
                                   config.USERNAME_INPUT_PLACEHOLDER)
        max_text_w = self.rect.width - 30
        txt_rect = txt.get_rect(midleft=(self.rect.x + 15, self.rect.centery))
        if txt.get_width() > max_text_w and self.text:
            txt_rect.right = self.rect.right - 15
        old_clip = screen.get_clip()
        screen.set_clip(self.rect.inflate(-10, 0))
        screen.blit(txt, txt_rect)
        screen.set_clip(old_clip)
        if self.focused and self._cursor_visible:
            cursor_x = min(txt_rect.right + 4, self.rect.right - 10) if self.text else txt_rect.left
            pygame.draw.line(screen, config.USERNAME_INPUT_CURSOR,
                             (cursor_x, self.rect.centery - 12),
                             (cursor_x, self.rect.centery + 12), 2)


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

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
    header = header_font.render("LEADERBOARD", True, config.UI_ACCENT)
    screen.blit(header,
                header.get_rect(center=(panel_x + panel_w // 2, panel_y + 22)))

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

    scores = score_manager.get_high_scores(10)
    row_start_y = panel_y + 66
    row_h = 36

    if not scores:
        ef = pygame.font.Font(config.FONT_PATH, 13)
        empty = ef.render("No scores yet!", True, config.UI_TEXT_SECONDARY)
        screen.blit(empty,
                    (panel_x + panel_w // 2 - empty.get_width() // 2,
                     row_start_y + 40))
        return

    entry_font = pygame.font.Font(config.FONT_PATH, 13)
    rank_font = pygame.font.Font(config.FONT_PATH, 14)

    for i, entry in enumerate(scores):
        row_y = row_start_y + i * row_h
        rank = i + 1

        if rank == 1:
            bg_c, rk_c = config.LEADERBOARD_GOLD_BG, config.LEADERBOARD_GOLD
        elif rank == 2:
            bg_c, rk_c = config.LEADERBOARD_SILVER_BG, config.LEADERBOARD_SILVER
        elif rank == 3:
            bg_c, rk_c = config.LEADERBOARD_BRONZE_BG, config.LEADERBOARD_BRONZE
        else:
            bg_c = config.LEADERBOARD_ROW_ALT if i % 2 == 0 \
                else config.LEADERBOARD_ROW_BG
            rk_c = config.UI_TEXT_SECONDARY

        row_surf = pygame.Surface((panel_w - 4, row_h), pygame.SRCALPHA)
        row_surf.fill(bg_c)
        screen.blit(row_surf, (panel_x + 2, row_y))

        rk = rank_font.render(str(rank), True, rk_c)
        screen.blit(rk, (panel_x + 20, row_y + row_h // 2 - rk.get_height() // 2))

        name = entry.get("player", "???")[:10]
        nm = entry_font.render(name, True, config.UI_TEXT_PRIMARY)
        screen.blit(nm, (panel_x + 52, row_y + row_h // 2 - nm.get_height() // 2))

        sc = entry_font.render(str(entry.get("score", 0)), True,
                               config.UI_TEXT_PRIMARY)
        screen.blit(sc, (panel_x + 168, row_y + row_h // 2 - sc.get_height() // 2))

        cb = entry_font.render(str(entry.get("max_combo", 0)), True,
                               config.SCORE_DISPLAY_COMBO)
        screen.blit(cb, (panel_x + 258, row_y + row_h // 2 - cb.get_height() // 2))


def _draw_panel(screen, rect, color):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill(color)
    screen.blit(panel, rect)


# ---------------------------------------------------------------------------
# Recording screen
# ---------------------------------------------------------------------------

def _run_recording(screen, config):
    clock = pygame.time.Clock()
    font_l = pygame.font.Font(config.FONT_PATH, 32)
    font_m = pygame.font.Font(config.FONT_PATH, 22)
    font_s = pygame.font.Font(config.FONT_PATH, 16)

    sw, sh = screen.get_width(), screen.get_height()
    pw, ph = 620, 460
    px = (sw - pw) // 2
    py = (sh - ph) // 2

    audio_input = TextInput((px + 80, py + 125, pw - 260, 38),
                            placeholder="Audio file path...", max_length=120)
    browse_btn = Button("BROWSE",
                        (px + pw - 165, py + 126, 85, 36),
                        config.UI_ACCENT, font_size=15)

    name_input = TextInput((px + 80, py + 210, pw - 160, 38),
                           placeholder="Level name...")

    start_btn = Button("START RECORDING",
                       (px + pw // 2 - 150, py + 300, 300, 52),
                       config.UI_BUTTON_START, font_size=20)
    back_btn = Button("BACK",
                      (px + pw // 2 - 100, py + ph - 65, 200, 44),
                      config.UI_BUTTON_EXIT, font_size=18)

    status_msg = ""
    status_timer = 0.0

    while True:
        dt = clock.tick(config.SCREEN_FPS) / 1000
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and not name_input.focused \
                        and not audio_input.focused:
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            audio_input.handle_event(event)
            name_input.handle_event(event)

        screen.fill((8, 8, 24))
        _draw_panel(screen, pygame.Rect(px, py, pw, ph), config.UI_PANEL)

        title = font_l.render("Record New Level", True, config.UI_TEXT_PRIMARY)
        screen.blit(title, title.get_rect(center=(sw // 2, py + 35)))

        # Audio file selection
        aud_lbl = font_m.render("Audio File", True, config.UI_TEXT_SECONDARY)
        screen.blit(aud_lbl, (px + 80, py + 90))
        audio_input.update(dt)
        audio_input.draw(screen, config)
        browse_btn.update(browse_btn.rect.collidepoint(mouse_pos), dt)
        browse_btn.draw(screen)

        # Level name
        nm_lbl = font_m.render("Level Name", True, config.UI_TEXT_SECONDARY)
        screen.blit(nm_lbl, (px + 80, py + 180))
        name_input.update(dt)
        name_input.draw(screen, config)

        start_btn.update(start_btn.rect.collidepoint(mouse_pos), dt)
        start_btn.draw(screen)
        back_btn.update(back_btn.rect.collidepoint(mouse_pos), dt)
        back_btn.draw(screen)

        if status_timer > 0:
            status_timer -= dt
            st = font_s.render(status_msg, True, config.COLOR_GREEN)
            screen.blit(st, st.get_rect(center=(sw // 2, py + 370)))

        if mouse_clicked:
            if back_btn.rect.collidepoint(mouse_pos):
                return
            if browse_btn.rect.collidepoint(mouse_pos):
                pygame.display.flip()
                picked = _pick_audio_file()
                if picked and os.path.exists(picked):
                    audio_input.text = picked
            if start_btn.rect.collidepoint(mouse_pos):
                audio_file = audio_input.text.strip()
                level_name = name_input.text.strip()
                if not audio_file or not os.path.exists(audio_file):
                    status_msg = "Select a valid audio file!"
                    status_timer = 2.0
                    continue
                if not level_name:
                    status_msg = "Enter a level name!"
                    status_timer = 2.0
                    continue

                notes = _record_chart(screen, config, audio_file)
                if notes:
                    path = _save_level(level_name, audio_file, notes)
                    status_msg = f"Saved: {path.name}"
                    status_timer = 3.0
                else:
                    status_msg = "Recording cancelled."
                    status_timer = 2.0

        pygame.display.flip()


def _record_chart(screen, config, audio_file):
    """Internal recording loop — returns list of note dicts."""
    clock = pygame.time.Clock()
    font = pygame.font.Font(config.FONT_PATH, 28)
    font_s = pygame.font.Font(config.FONT_PATH, 20)

    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.set_volume(config.MUSIC_VOLUME)
    pygame.mixer.music.play()
    start_time = time.monotonic()

    notes = []
    running = True

    while running:
        now = time.monotonic() - start_time
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_u and notes:
                    notes.pop()
                elif event.key == pygame.K_0:
                    for lane in range(5):
                        notes.append({"lane": lane,
                                      "time_seconds": round(now, 4),
                                      "kind": "chord"})
                elif pygame.K_1 <= event.key <= pygame.K_5:
                    lane = event.key - pygame.K_1
                    notes.append({"lane": lane,
                                  "time_seconds": round(now, 4),
                                  "kind": "tap"})

        screen.fill((8, 8, 24))
        overlay_bar = pygame.Surface((screen.get_width(), 80), pygame.SRCALPHA)
        overlay_bar.fill((0, 0, 0, 200))
        screen.blit(overlay_bar, (0, screen.get_height() - 80))

        status = font.render(
            f"Recording...  Time: {now:.1f}s  Notes: {len(notes)}",
            True, (255, 255, 255))
        hint = font_s.render("1-5 lane | 0 chord | U undo | Q save & quit",
                             True, (180, 180, 180))
        screen.blit(status, (20, screen.get_height() - 70))
        screen.blit(hint, (20, screen.get_height() - 40))
        pygame.display.flip()
        clock.tick(60)

    pygame.mixer.music.stop()
    return notes


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def run_settings(screen, config):
    clock = pygame.time.Clock()
    font_l = pygame.font.Font(config.FONT_PATH, 32)
    font_m = pygame.font.Font(config.FONT_PATH, 22)
    font_s = pygame.font.Font(config.FONT_PATH, 16)
    font_xs = pygame.font.Font(config.FONT_PATH, 13)

    sw, sh = screen.get_width(), screen.get_height()
    pw, ph = 640, 650
    px = (sw - pw) // 2
    py = (sh - ph) // 2

    slider = Slider((px + 60, py + 85, pw - 120, 28),
                    min_val=0.0, max_val=1.0, start_val=config.MUSIC_VOLUME)
    name_input = TextInput((px + 60, py + 145, pw - 120, 38),
                           placeholder="Enter your name...")
    name_input.text = config.USERNAME

    levels = _list_levels()
    selected_level = config.SELECTED_LEVEL

    back_btn = Button("BACK",
                      (px + pw // 2 - 100, py + ph - 60, 200, 44),
                      config.UI_BUTTON_EXIT, font_size=18)
    browse_btn = Button("BROWSE MUSIC",
                        (px + 60, py + 270, 170, 38),
                        config.UI_ACCENT, font_size=16)
    record_btn = Button("RECORD LEVEL",
                        (px + 250, py + 270, 170, 38),
                        config.UI_BUTTON_SETTINGS, font_size=16)

    current_file = config.AUDIO_FILE
    status_msg = ""
    status_timer = 0.0

    while True:
        dt = clock.tick(config.SCREEN_FPS) / 1000
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

        levels = _list_levels()

        screen.fill(config.COLOR_BLACK)
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((8, 8, 24, 255))
        screen.blit(overlay, (0, 0))
        _draw_panel(screen, pygame.Rect(px, py, pw, ph), config.UI_PANEL)

        t = font_l.render("Settings", True, config.UI_TEXT_PRIMARY)
        screen.blit(t, t.get_rect(center=(sw // 2, py + 30)))

        # Volume
        vl = font_m.render(f"Volume: {int(slider.value * 100)}%", True,
                           config.UI_TEXT_SECONDARY)
        screen.blit(vl, (px + 60, py + 55))
        slider.draw(screen, config)

        # Name
        nl = font_m.render("Your Name", True, config.UI_TEXT_SECONDARY)
        screen.blit(nl, (px + 60, py + 115))
        name_input.update(dt)
        name_input.draw(screen, config)

        # Music track
        ml = font_m.render("Game Music", True, config.UI_TEXT_SECONDARY)
        screen.blit(ml, (px + 60, py + 200))
        if current_file:
            short = os.path.basename(current_file)
        else:
            short = "No file selected"
        mt = font_s.render(short, True, config.UI_TEXT_PRIMARY)
        screen.blit(mt, (px + 60, py + 235))

        # Level selection
        ll = font_m.render("Manual Level", True, config.UI_TEXT_SECONDARY)
        screen.blit(ll, (px + 60, py + 335))

        level_area_y = py + 365
        max_visible = 3
        row_h = 28

        if levels:
            for i, lvl_name in enumerate(levels[:max_visible]):
                row_y = level_area_y + i * row_h
                is_sel = lvl_name == selected_level
                row_surf = pygame.Surface((pw - 160, row_h), pygame.SRCALPHA)
                if is_sel:
                    row_surf.fill(config.LEADERBOARD_ROW_ALT)
                screen.blit(row_surf, (px + 60, row_y))

                txt_c = config.UI_ACCENT if is_sel else config.UI_TEXT_PRIMARY
                lvl_txt = font_xs.render(lvl_name, True, txt_c)
                screen.blit(lvl_txt, (px + 70, row_y + 4))
        else:
            empty = font_s.render("No levels recorded yet", True,
                                  (100, 100, 130))
            screen.blit(empty, (px + 60, level_area_y + 6))

        # Mode indicator
        mode_text = "Random (Auto)" if not selected_level \
            else f"Manual: {selected_level}"
        mode_c = config.UI_TEXT_SECONDARY if not selected_level \
            else config.UI_ACCENT
        mt2 = font_s.render(mode_text, True, mode_c)
        screen.blit(mt2, (px + 60, level_area_y + max_visible * row_h + 8))

        hover_back = back_btn.rect.collidepoint(mouse_pos)
        hover_browse = browse_btn.rect.collidepoint(mouse_pos)
        hover_record = record_btn.rect.collidepoint(mouse_pos)

        back_btn.update(hover_back, dt)
        browse_btn.update(hover_browse, dt)
        record_btn.update(hover_record, dt)
        back_btn.draw(screen)
        browse_btn.draw(screen)
        record_btn.draw(screen)

        if status_timer > 0:
            status_timer -= dt
            st = font_s.render(status_msg, True, config.COLOR_GREEN)
            screen.blit(st, st.get_rect(center=(sw // 2, py + ph - 85)))

        if mouse_clicked:
            if back_btn.rect.collidepoint(mouse_pos):
                config.MUSIC_VOLUME = slider.value
                config.USERNAME = name_input.text.strip()
                config.SELECTED_LEVEL = selected_level
                return "back", config
            if browse_btn.rect.collidepoint(mouse_pos):
                pygame.display.flip()
                picked = _pick_audio_file()
                if picked and os.path.exists(picked):
                    current_file = picked
                    config.AUDIO_FILE = picked
                    status_msg = "Track selected!"
                    status_timer = 3.0
                elif picked:
                    status_msg = "File not found."
                    status_timer = 2.0
            if record_btn.rect.collidepoint(mouse_pos):
                _run_recording(screen, config)
                levels = _list_levels()

            if levels:
                for i, lvl_name in enumerate(levels[:max_visible]):
                    row_rect = pygame.Rect(px + 60,
                                           level_area_y + i * row_h,
                                           pw - 160, row_h)
                    if row_rect.collidepoint(mouse_pos):
                        selected_level = "" if selected_level == lvl_name \
                            else lvl_name

        config.MUSIC_VOLUME = slider.value
        config.USERNAME = name_input.text.strip()
        pygame.display.flip()


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def run_menu(screen, config, score_manager):
    clock = pygame.time.Clock()
    font_title = pygame.font.Font(config.FONT_PATH, 48)
    font_sub = pygame.font.Font(config.FONT_PATH, 16)
    font_msg = pygame.font.Font(config.FONT_PATH, 18)

    cx = screen.get_width() // 2
    cy = screen.get_height() // 2 + 20
    bw, bh, gap = 320, 76, 18

    start_btn = MenuButton("START",
                           (cx - bw // 2, cy - 40, bw, bh),
                           config.UI_BUTTON_START)
    settings_btn = MenuButton("SETTINGS",
                              (cx - bw // 2, cy + bh - 40 + gap, bw, bh),
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
        dt = clock.tick(config.SCREEN_FPS) / 1000
        title_anim += dt

        has_name = bool(config.USERNAME.strip())
        has_music = bool(config.AUDIO_FILE) and os.path.exists(config.AUDIO_FILE)
        has_level = bool(config.SELECTED_LEVEL)
        can_start = has_name and (has_music or has_level)
        start_btn.enabled = can_start

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

        if has_level:
            track_name = f"Level: {config.SELECTED_LEVEL}"
            track_color = config.UI_ACCENT
            track_info = font_sub.render(track_name, True, track_color)
            screen.blit(track_info, track_info.get_rect(center=(cx, 133)))
        else:
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
            if not has_music and not has_level:
                msgs.append("Select music or manual level in Settings")
            warn = font_msg.render(" | ".join(msgs), True,
                                   config.UI_TEXT_WARN)
            screen.blit(warn,
                        warn.get_rect(center=(cx, start_btn.rect.top - 20)))

        if status_timer > 0:
            status_timer -= dt
            msg = font_msg.render(status_text, True, config.UI_TEXT_WARN)
            screen.blit(msg, msg.get_rect(
                center=(cx, exit_btn.rect.bottom + 30)))

        if not hasattr(display_user_camera, 'tracker') or \
                not display_user_camera.tracker:
            for btn in menu_buttons:
                btn.update(False, dt)
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
            btn.update(hovered, dt)
            btn.draw(screen)

            inside = any(btn.point_inside(p) for p in finger_positions)
            if inside and btn.armed:
                btn.armed = False
                action = actions[btn]
                draw_finger_indicators(screen, hand0_pos, hand1_pos)
                pygame.display.flip()

                if action == "settings":
                    release_camera_tracker()
                    result, config = run_settings(screen, config)
                    if result == "exit":
                        return "", "exit"
                elif action == "start":
                    if not config.AUDIO_FILE or \
                            not os.path.exists(config.AUDIO_FILE):
                        if not config.SELECTED_LEVEL:
                            status_text = "Select music or manual level first!"
                            status_timer = 2.0
                            btn.armed = True
                            continue
                    if not config.USERNAME.strip():
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
