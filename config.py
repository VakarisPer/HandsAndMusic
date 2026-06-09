import math


class GameConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    SCREEN_FPS = 60

    AUDIO_FILE = ""
    MUSIC_VOLUME = 0.7
    USE_MUSIC_SPAWNER = True
    BEAT_SKIP = 2
    BURST_INTERVAL = 16
    SPAWN_INTERVAL = 0.8

    TILE_SIZE = 30
    TILE_SPEED = 250
    TILE_SPAWN_Y = -50
    KICK_TILE_SPEED = 250
    SPAWN_PATTERN = "random"

    CATCHER_SIZE = 40
    CATCHER_LANE_SPACING = 100
    CATCHER_LANE_WIDTH = 75
    TILE_CATCH_ZONE_HEIGHT = 130
    CATCHER_POINTER_RADIUS = 40
    CATCHER_COLLISION_RADIUS = 50
    CATCHER_EXPANSION_EFFECT = 5
    FEEDBACK_DURATION = 0.3

    POINTS_PER_CATCH = 10
    POINTS_PER_MISS = 5
    POINTS_PER_BAD_CLICK = 5
    GOLDEN_TILE_POINTS = 200
    GOLDEN_TILE_CHANCE = 0.06

    PARTICLE_COUNT = 12
    PARTICLE_SPEED_MIN = 40
    PARTICLE_SPEED_MAX = 180
    PARTICLE_SIZE_MIN = 1.5
    PARTICLE_SIZE_MAX = 5
    PARTICLE_LIFETIME = 0.8

    HAND_DETECTION_CONFIDENCE = 0.55
    HAND_TRACKING_CONFIDENCE = 0.5

    SCORES_FILE = "scores.json"
    FONT_PATH = "fonts/RobotikaPixelGreek-nAWJR.otf"

    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_RED = (255, 0, 0)
    COLOR_GREEN = (0, 255, 0)
    COLOR_BLUE = (0, 0, 255)
    COLOR_YELLOW = (255, 255, 0)
    COLOR_ORANGE = (255, 100, 0)
    COLOR_MAGENTA = (255, 0, 255)
    COLOR_CYAN = (0, 255, 255)
    COLOR_BURST = (180, 100, 255)
    COLOR_GOLDEN = (255, 215, 0)
    COLOR_GOLDEN_GLOW = (255, 240, 100)

    UI_BG_OVERLAY = (0, 0, 0, 160)
    UI_PANEL = (15, 15, 35, 230)
    UI_ACCENT = (80, 180, 255)
    UI_ACCENT_HOVER = (120, 210, 255)
    UI_BUTTON_START = (34, 180, 74)
    UI_BUTTON_EXIT = (200, 55, 55)
    UI_BUTTON_SETTINGS = (55, 55, 200)
    UI_SLIDER_TRACK = (50, 50, 70)
    UI_SLIDER_FILL = (80, 180, 255)
    UI_SLIDER_KNOB = (230, 230, 245)
    UI_TEXT_PRIMARY = (245, 245, 255)
    UI_TEXT_SECONDARY = (160, 175, 195)
    UI_TEXT_WARN = (255, 140, 100)

    @staticmethod
    def rainbow_color(t, saturation=1.0, brightness=1.0):
        r = int((math.sin(t) * 0.5 + 0.5) * 255 * brightness * saturation)
        g = int((math.sin(t + 2.094) * 0.5 + 0.5) * 255 * brightness * saturation)
        b = int((math.sin(t + 4.189) * 0.5 + 0.5) * 255 * brightness * saturation)
        return (r, g, b)
