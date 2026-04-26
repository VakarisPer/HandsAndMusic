"""Game configuration constants (Singleton)."""


class GameConfig:
    """Single source of truth for tunable game parameters."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ---- Display ---------------------------------------------------------
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    SCREEN_FPS = 60

    # ---- Audio / music spawning -----------------------------------------
    AUDIO_FILE = "audio/Notion.mp3"
    USE_MUSIC_SPAWNER = True   # True = sync to detected BPM, False = timer
    BEAT_SKIP = 2              # Spawn one tile every Nth beat
    BURST_INTERVAL = 16        # Every Nth beat spawn a 5-tile row (0 = off)
    SPAWN_INTERVAL = 0.8       # Fallback timer when music spawner is off

    # ---- Tiles ----------------------------------------------------------
    TILE_SIZE = 30
    TILE_SPEED = 250           # Fixed pixels/second (rhythm sync)
    TILE_SPAWN_Y = -50         # Y where tiles spawn (off-screen top)
    KICK_TILE_SPEED = 250      # Visual variant; speed must match TILE_SPEED
    SPAWN_PATTERN = "random"   # sequential | random | alternating |
                               # center_first | zigzag

    # ---- Catchers -------------------------------------------------------
    CATCHER_SIZE = 40
    CATCHER_LANE_SPACING = 100
    CATCHER_LANE_WIDTH = 75            # Horizontal width of an Open_Palm lane
    TILE_CATCH_ZONE_HEIGHT = 130       # How tall the bottom catch band is
    CATCHER_POINTER_RADIUS = 40        # Finger-to-catcher click radius
    CATCHER_COLLISION_RADIUS = 50      # Catcher-to-tile catch radius
    CATCHER_EXPANSION_EFFECT = 5       # Pulse size on activation
    FEEDBACK_DURATION = 0.3            # Seconds the green/red flash lasts

    # ---- Scoring --------------------------------------------------------
    POINTS_PER_CATCH = 1
    POINTS_PER_MISS = 1        # Subtracted when a tile drops off screen
    POINTS_PER_BAD_CLICK = 1   # Subtracted for clicking on missed tile

    # ---- Hand tracking --------------------------------------------------
    HAND_DETECTION_CONFIDENCE = 0.55
    HAND_TRACKING_CONFIDENCE = 0.5

    # ---- Files ----------------------------------------------------------
    SCORES_FILE = "scores.json"

    # ---- Colors (RGB) ---------------------------------------------------
    COLOR_WHITE   = (255, 255, 255)
    COLOR_BLACK   = (0, 0, 0)
    COLOR_RED     = (255, 0, 0)
    COLOR_GREEN   = (0, 255, 0)
    COLOR_BLUE    = (0, 0, 255)
    COLOR_YELLOW  = (255, 255, 0)
    COLOR_ORANGE  = (255, 100, 0)       # Kick tiles
    COLOR_MAGENTA = (255, 0, 255)       # Hand 1 finger indicator
    COLOR_CYAN    = (0, 255, 255)       # Hand 0 finger indicator
    COLOR_BURST   = (180, 100, 255)     # 5-tile row (palm-only)
