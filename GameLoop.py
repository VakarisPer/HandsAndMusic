"""
Main game loop for Hand Gesture-Controlled Rhythm Game.

Handles game object management (tiles + catchers), hand gesture collision,
scoring with combo multiplier, optional music-synced spawning, and rendering.
"""

import random
from abc import ABC, abstractmethod

import pygame
import cv2

from hand_tracking.Tracking import HandTracker
from config import GameConfig
from score_manager import ScoreManager


# ---------------------------------------------------------------------------
# Game objects (OOP hierarchy with abstract base)
# ---------------------------------------------------------------------------

class GameObject(ABC):
    """Abstract base class for all on-screen game entities."""

    def __init__(self, name, position, size, color, speed, list_ref=None):
        self.name = name
        self.position = position
        self.size = size
        self.color = color
        self.original_color = color
        self.speed = speed
        self.list_ref = list_ref
        self.click_effect = 0
        self.feedback_color = None
        self.feedback_timer = 0

    @abstractmethod
    def update(self, dt):
        """Per-frame state update. Subclasses define their own behavior."""
        ...

    def delete(self):
        if self.list_ref is not None and self in self.list_ref:
            self.list_ref.remove(self)

    def get_display_size(self):
        return self.size + (self.click_effect * 5)

    def point_collision(self, point_x, point_y, radius=30):
        """Circle-vs-point collision against this object's center."""
        center_x = self.position.x + self.size / 2
        center_y = self.position.y + self.size / 2
        dx = point_x - center_x
        dy = point_y - center_y
        distance = (dx * dx + dy * dy) ** 0.5
        return distance < (self.size / 2 + radius)

    def collision(self, other):
        """AABB rectangle overlap test."""
        return not (
            self.position.x + self.size < other.position.x
            or self.position.x > other.position.x + other.size
            or self.position.y + self.size < other.position.y
            or self.position.y > other.position.y + other.size
        )


class Tile(GameObject):
    """Falling tile.

    `is_kick` and `is_burst` are visual/gameplay markers:
      * is_kick   — orange variant on kick beats (caught like a normal tile)
      * is_burst  — part of a 5-tile row, ONLY catchable with Open_Palm
    """

    def __init__(self, tile_id, position, color, speed,
                 list_ref=None, is_kick=False, is_burst=False):
        super().__init__(
            f"tile_{tile_id}", position, GameConfig.TILE_SIZE,
            color, speed, list_ref,
        )
        self.is_kick = is_kick
        self.is_burst = is_burst

    def update(self, dt):
        self.position.y += self.speed * dt


class Catcher(GameObject):
    """Stationary lane catcher. Pulses on activation.

    Holds per-hand 'armed' state so a click only registers when a finger
    enters the catcher; the finger must leave before the next click.
    """

    def __init__(self, lane_index, position, list_ref=None):
        super().__init__(
            f"catcher_{lane_index}", position, GameConfig.CATCHER_SIZE,
            GameConfig.COLOR_WHITE, 0, list_ref,
        )
        self.lane_index = lane_index
        self.pointer_armed = [True, True]  # one slot per tracked hand

    def update(self, dt):
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
        if self.click_effect > 0:
            self.click_effect -= 1


# ---------------------------------------------------------------------------
# Spawners
# ---------------------------------------------------------------------------

class TileSpawner:
    """Creates tiles in lanes using selectable patterns."""

    PATTERNS = {
        "sequential":   lambda count: count % 5,
        "alternating":  lambda count: [0, 4, 1, 3, 2][count % 5],
        "center_first": lambda count: [2, 1, 3, 0, 4][count % 5],
        "zigzag":       lambda count: [0, 2, 4, 3, 1][count % 5],
        "random":       lambda count: random.randint(0, 4),
    }

    TILE_COLORS = [
        GameConfig.COLOR_RED, GameConfig.COLOR_GREEN, GameConfig.COLOR_BLUE,
        GameConfig.COLOR_YELLOW, GameConfig.COLOR_MAGENTA,
    ]

    def __init__(self, screen_width, lane_positions):
        self.screen_width = screen_width
        self.lane_positions = lane_positions
        self.spawn_count = 0

    def spawn_tile(self, tiles, pattern="sequential", is_kick=False):
        """Spawn one normal tile in a lane chosen by `pattern`."""
        pattern_fn = self.PATTERNS.get(pattern, self.PATTERNS["sequential"])
        lane_index = pattern_fn(self.spawn_count)
        self.spawn_count += 1
        self._make_tile(tiles, lane_index, is_kick=is_kick, is_burst=False)

    def spawn_row(self, tiles):
        """Spawn one BURST tile in every lane (only Open_Palm catches them)."""
        for lane_index in range(len(self.lane_positions)):
            self.spawn_count += 1
            self._make_tile(tiles, lane_index, is_kick=False, is_burst=True)

    def _make_tile(self, tiles, lane_index, is_kick, is_burst):
        position = pygame.math.Vector2(self.lane_positions[lane_index],
                                       GameConfig.TILE_SPAWN_Y)
        if is_burst:
            color = GameConfig.COLOR_BURST
            speed = GameConfig.TILE_SPEED
        elif is_kick:
            color = GameConfig.COLOR_ORANGE
            speed = GameConfig.KICK_TILE_SPEED
        else:
            color = random.choice(self.TILE_COLORS)
            speed = GameConfig.TILE_SPEED
        tiles.append(Tile(self.spawn_count, position, color, speed,
                          tiles, is_kick=is_kick, is_burst=is_burst))


class MusicSpawner:
    """Spawns tiles so they hit the catcher row on the beat.

    BPM is detected once by librosa, then beats are generated as a fixed
    interval grid (60 / bpm). Every Nth beat (BEAT_SKIP) gets a tile,
    spawned `travel_time` seconds early so it arrives on the beat.
    """

    def __init__(self, tile_spawner, bpm, travel_time,
                 beat_skip=1, burst_interval=0):
        self.tile_spawner = tile_spawner
        self.beat_interval = 60.0 / max(bpm, 1)
        self.travel_time = travel_time
        self.beat_skip = max(1, int(beat_skip))
        self.burst_interval = max(0, int(burst_interval))
        # Skip every beat whose pre-spawn time would be before the song
        # started — otherwise the game floods with random tiles on launch.
        self.next_beat_index = 0
        while (self.next_beat_index * self.beat_interval
               - self.travel_time < 0):
            self.next_beat_index += 1

    def update(self, current_song_time, tiles, pattern):
        """Spawn any tiles whose lead-time window has now arrived."""
        while True:
            beat_time = self.next_beat_index * self.beat_interval
            spawn_time = beat_time - self.travel_time
            if current_song_time < spawn_time:
                return
            if self.next_beat_index % self.beat_skip == 0:
                if (self.burst_interval
                        and self.next_beat_index > 0
                        and self.next_beat_index % self.burst_interval == 0):
                    self.tile_spawner.spawn_row(tiles)
                else:
                    self.tile_spawner.spawn_tile(tiles, pattern)
            self.next_beat_index += 1


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def display_user_camera(screen, tracker):
    frame = tracker.get_frame()
    if frame is None:
        return
    frame_resized = cv2.resize(frame, (screen.get_width(), screen.get_height()))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    surface = pygame.image.fromstring(
        frame_rgb.tobytes(), frame_rgb.shape[1::-1], 'RGB',
    )
    screen.blit(surface, (0, 0))


def _draw_finger_marker(screen, pos, color):
    if pos is None:
        return
    x, y = int(pos[0]), int(pos[1])
    pygame.draw.circle(screen, color, (x, y), 15, 2)
    pygame.draw.line(screen, color, (x - 20, y), (x + 20, y), 2)
    pygame.draw.line(screen, color, (x, y - 20), (x, y + 20), 2)


def draw_finger_indicators(screen, hand0_pos, hand1_pos):
    _draw_finger_marker(screen, hand0_pos, GameConfig.COLOR_CYAN)
    _draw_finger_marker(screen, hand1_pos, GameConfig.COLOR_MAGENTA)


def draw_game_objects(screen, tiles, catchers, dt):
    """Update + render all game objects (movement now lives on the objects)."""
    for tile in tiles:
        tile.update(dt)
        pygame.draw.rect(screen, tile.color,
                         (tile.position.x, tile.position.y,
                          tile.size, tile.size))

    for catcher in catchers:
        catcher.update(dt)
        display_size = catcher.get_display_size()
        offset = (display_size - catcher.size) / 2
        color = (catcher.feedback_color
                 if catcher.feedback_timer > 0 else catcher.original_color)
        pygame.draw.rect(screen, color,
                         (catcher.position.x - offset,
                          catcher.position.y - offset,
                          display_size, display_size))


def draw_ui(screen, score, combo, font):
    score_text = font.render(f"Score: {score}", True, GameConfig.COLOR_WHITE)
    screen.blit(score_text, (20, 20))
    if combo > 1:
        combo_text = font.render(f"Combo x{combo}", True,
                                 GameConfig.COLOR_ORANGE)
        screen.blit(combo_text, (20, 70))


# ---------------------------------------------------------------------------
# Per-frame collision logic (extracted to remove hand-0 / hand-1 duplication)
# ---------------------------------------------------------------------------

def _screen_pos_from_finger(finger_pos, screen):
    if finger_pos is None:
        return None
    return (finger_pos[0] * screen.get_width(),
            finger_pos[1] * screen.get_height())


def _handle_pointer_collision(finger_pos, hand_index,
                              catchers, tiles, frame_state, config):
    """One hand's pointer click. Click only fires on enter; finger must
    leave the catcher before another click is registered (no spam-hold).
    """
    if finger_pos is None:
        # Re-arm every catcher for this hand when the hand isn't tracked
        for catcher in catchers:
            catcher.pointer_armed[hand_index] = True
        return

    for i, catcher in enumerate(catchers):
        inside = catcher.point_collision(
            finger_pos[0], finger_pos[1], config.CATCHER_POINTER_RADIUS,
        )
        if not inside:
            catcher.pointer_armed[hand_index] = True
            continue
        if not catcher.pointer_armed[hand_index]:
            continue  # Still inside from a previous click — ignore

        # Fresh click
        catcher.pointer_armed[hand_index] = False
        catcher.click_effect = config.CATCHER_EXPANSION_EFFECT
        frame_state["used"].add(i)

        for tile in tiles[:]:
            if tile.is_burst:
                continue  # Burst tiles can only be caught with Open_Palm
            if catcher.point_collision(
                tile.position.x + tile.size / 2,
                tile.position.y + tile.size / 2,
                config.CATCHER_COLLISION_RADIUS,
            ):
                frame_state["had_tiles"].add(i)
                if tile not in frame_state["to_remove"]:
                    frame_state["to_remove"].append(tile)
                    frame_state["caught"].add(i)


def _handle_open_palm(catchers, tiles, frame_state, screen_height, config):
    """Open_Palm catches BURST tiles only — never single tiles."""
    for i, catcher in enumerate(catchers):
        catcher.click_effect = config.CATCHER_EXPANSION_EFFECT
        frame_state["used"].add(i)
        for tile in tiles[:]:
            if not tile.is_burst:
                continue
            in_zone = tile.position.y > (screen_height
                                         - config.TILE_CATCH_ZONE_HEIGHT)
            in_lane = abs(tile.position.x - catcher.position.x) \
                      < config.CATCHER_LANE_WIDTH
            if in_zone and in_lane:
                frame_state["had_tiles"].add(i)
                if tile not in frame_state["to_remove"]:
                    frame_state["to_remove"].append(tile)
                    frame_state["caught"].add(i)


def _drop_missed_tiles(tiles, screen_height, config):
    """Remove off-screen tiles. Returns (score_penalty, missed_count)."""
    penalty = 0
    count = 0
    for tile in tiles[:]:
        if tile.position.y > screen_height:
            tile.delete()
            penalty += config.POINTS_PER_MISS
            count += 1
    return penalty, count


def _resolve_score(catchers, frame_state, score, combo, config):
    """Apply per-frame score + combo. Returns (new_score, new_combo)."""
    for i, catcher in enumerate(catchers):
        if i not in frame_state["used"]:
            continue
        if i in frame_state["caught"]:
            score += config.POINTS_PER_CATCH
            combo += 1
            catcher.feedback_color = config.COLOR_GREEN
            catcher.feedback_timer = config.FEEDBACK_DURATION
        elif i in frame_state["had_tiles"]:
            score -= config.POINTS_PER_BAD_CLICK
            combo = 0
            catcher.feedback_color = config.COLOR_RED
            catcher.feedback_timer = config.FEEDBACK_DURATION
    return score, combo


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

def _build_catchers(screen, lane_positions):
    catchers = [
        Catcher(i, pygame.math.Vector2(
            lane_positions[i] - 5, screen.get_height() - 100,
        ))
        for i in range(5)
    ]
    for catcher in catchers:
        catcher.list_ref = catchers
    return catchers


def _build_music_spawner(tile_spawner, travel_time, bpm, config):
    """Start playback and return a MusicSpawner. BPM is detected up-front
    (before the menu) so the game launches without delay."""
    if bpm is None:
        return None, None
    try:
        from audio import play_audio
        start_time = play_audio(config.AUDIO_FILE)
        spawner = MusicSpawner(tile_spawner, bpm, travel_time,
                               beat_skip=config.BEAT_SKIP,
                               burst_interval=config.BURST_INTERVAL)
        return spawner, start_time
    except Exception as e:
        print(f"[Game] Music spawner disabled: {e}")
        return None, None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_game(screen, tracker, config, bpm=None):
    """One game session. Caller owns the screen + tracker lifecycle.

    `bpm` is detected up-front by start() so the game starts instantly.
    """
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 48)
    score_manager = ScoreManager(config.SCORES_FILE)

    center_x = screen.get_width() / 2
    lane_positions = [center_x + (i - 2) * config.CATCHER_LANE_SPACING
                      for i in range(5)]
    catchers = _build_catchers(screen, lane_positions)
    tiles = []

    tile_spawner = TileSpawner(screen.get_width(), lane_positions)

    # How long a tile takes to travel from spawn to the catcher row.
    # MusicSpawner pre-spawns by exactly this much so the tile lands on-beat.
    catcher_y = screen.get_height() - 100
    travel_distance = catcher_y - config.TILE_SPAWN_Y
    travel_time = travel_distance / config.TILE_SPEED

    music_spawner, music_start = (None, None)
    if config.USE_MUSIC_SPAWNER:
        music_spawner, music_start = _build_music_spawner(
            tile_spawner, travel_time, bpm, config)

    spawn_timer = 0
    score = 0
    combo = 0
    dt = 0
    running = True
    palm_armed = [True, True]  # Open_Palm also debounced per hand

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(config.COLOR_BLACK)
        display_user_camera(screen, tracker)

        if not tracker.process_frame():
            continue

        gesture_0 = tracker.get_gesture_name(0)
        gesture_1 = tracker.get_gesture_name(1)
        hand0_pos = _screen_pos_from_finger(
            tracker.get_finger_position(0, finger_index=8), screen)
        hand1_pos = _screen_pos_from_finger(
            tracker.get_finger_position(1, finger_index=8), screen)

        frame_state = {
            "used": set(),
            "caught": set(),
            "had_tiles": set(),
            "to_remove": [],
        }

        # Debounce Open_Palm per hand: must release before next trigger.
        palm_fires = False
        for h, gesture in enumerate((gesture_0, gesture_1)):
            if gesture == "Open_Palm":
                if palm_armed[h]:
                    palm_fires = True
                    palm_armed[h] = False
            else:
                palm_armed[h] = True
        if palm_fires:
            _handle_open_palm(catchers, tiles, frame_state,
                              screen.get_height(), config)

        _handle_pointer_collision(hand0_pos, 0, catchers, tiles,
                                  frame_state, config)
        _handle_pointer_collision(hand1_pos, 1, catchers, tiles,
                                  frame_state, config)

        for tile in frame_state["to_remove"]:
            tile.delete()

        score, combo = _resolve_score(catchers, frame_state,
                                      score, combo, config)
        penalty, missed_count = _drop_missed_tiles(
            tiles, screen.get_height(), config)
        score -= penalty
        if missed_count > 0:
            combo = 0

        draw_game_objects(screen, tiles, catchers, dt)
        draw_finger_indicators(screen, hand0_pos, hand1_pos)
        draw_ui(screen, score, combo, font)

        pygame.display.flip()
        dt = clock.tick(config.SCREEN_FPS) / 1000

        # Spawn next tile(s)
        if music_spawner is not None:
            from audio import get_current_time
            music_spawner.update(get_current_time(music_start),
                                 tiles, config.SPAWN_PATTERN)
        else:
            spawn_timer += dt
            if spawn_timer >= config.SPAWN_INTERVAL:
                tile_spawner.spawn_tile(tiles, config.SPAWN_PATTERN)
                spawn_timer = 0

        print(f"Score: {score} | Combo: {combo} | "
              f"FPS: {clock.get_fps():.0f}")

    score_manager.add_score(score)
    if music_spawner is not None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
    return score


def start():
    """Top-level entry: analyze music → open window → menu → game loop."""
    from menu import run_menu

    config = GameConfig()

    # Analyze music BEFORE opening the window so the menu shows up
    # responsive (librosa can take a few seconds on first load).
    bpm = None
    if config.USE_MUSIC_SPAWNER:
        try:
            from audio import detect_bpm
            bpm = detect_bpm(config.AUDIO_FILE)
        except Exception as e:
            print(f"[Game] BPM detection failed, music disabled: {e}")

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH,
                                      config.SCREEN_HEIGHT))
    pygame.display.set_caption("Hand Gesture-Controlled Rhythm Game")

    tracker = HandTracker(
        detection_confidence=config.HAND_DETECTION_CONFIDENCE,
        tracking_confidence=config.HAND_TRACKING_CONFIDENCE,
    )

    try:
        while True:
            choice = run_menu(screen, tracker, config)
            if choice != "start":
                break
            run_game(screen, tracker, config, bpm=bpm)
    finally:
        tracker.release()
        pygame.quit()
