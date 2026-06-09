import pygame
import random
import audio
from hand_tracking.Tracking import HandTracker
import cv2
import numpy as np

tile_id = 0  # global counter

class GameObject:
    def __init__(self, name, position, size, color, speed, list_ref=None):
        self.name = name
        self.position = position
        self.size = size
        self.color = color
        self.original_color = color  # Store original color
        self.speed = speed
        self.list_ref = list_ref  # Reference to the shared list
        self.click_effect = 0  # Timer for click expansion effect
        self.pointer_collision = False  # Finger pointer collision this frame
        self.feedback_color = None  # Color feedback (red/green) for action feedback
        self.feedback_timer = 0  # Timer for feedback color display

    def delete(self):
        self.list_ref.remove(self)  # Removes itself from the list
    
    def get_display_size(self):
        """Return current display size, accounting for click effect"""
        return self.size + (self.click_effect * 5)
    
    def point_collision(self, point_x, point_y, radius=30):
        """Check if a point (finger) collides with this object"""
        # Circle collision
        center_x = self.position.x + self.size / 2
        center_y = self.position.y + self.size / 2
        
        dx = point_x - center_x
        dy = point_y - center_y
        distance = (dx**2 + dy**2)**0.5
        
        return distance < (self.size / 2 + radius)
    
    def collision(self, obj):
        """Check rectangular collision between this object and another object"""
        # Get bounding boxes
        self_left = self.position.x
        self_right = self.position.x + self.size
        self_top = self.position.y
        self_bottom = self.position.y + self.size
        
        obj_left = obj.position.x
        obj_right = obj.position.x + obj.size
        obj_top = obj.position.y
        obj_bottom = obj.position.y + obj.size
        
        # AABB collision detection
        return not (self_right < obj_left or self_left > obj_right or 
                   self_bottom < obj_top or self_top > obj_bottom)

class MusicSpawner:
    """Spawns tiles based on music beats"""
    def __init__(self, beat_times, kick_times, screen_width):
        self.beat_times = beat_times
        self.kick_times = set(kick_times)  # Convert to set for O(1) lookup
        self.screen_width = screen_width
        self.beat_index = 0
        self.spawn_window = 0.1  # ±100ms window to trigger spawn
    
    def should_spawn_tile(self, current_time):
        """
        Check if it's time to spawn a tile based on beats
        Returns: (should_spawn, is_kick)
        """
        if self.beat_index >= len(self.beat_times):
            return False, False
        
        beat_time = self.beat_times[self.beat_index]
        
        # If current time is within spawn window of next beat
        if current_time >= beat_time - self.spawn_window:
            self.beat_index += 1
            # Check if this beat corresponds to a kick
            is_kick = beat_time in self.kick_times
            return True, is_kick
        
        return False, False
    
    def spawn_tiles(self, tiles, current_time):
        """Spawn tiles for any beats that should happen now"""
        spawned = False
        while True:
            should_spawn, is_kick = self.should_spawn_tile(current_time)
            if not should_spawn:
                break
            
            spawned = True
            # Spawn more tiles on kicks (extra challenge)
            num_tiles = 2 if is_kick else 1
            
            for _ in range(num_tiles):
                tile_name = f"tile_{self.beat_index}_{_}"
                tile_position = pygame.math.Vector2(self.screen_width / 2, -50)
                
                # Kick tiles are special (different color/speed)
                if is_kick:
                    tile_color = (255, 100, 0)  # Orange for kick
                    tile_speed = random.randint(150, 170)  # Faster
                else:
                    tile_color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)])
                    tile_speed = random.randint(100, 110)

                new_tile = GameObject(tile_name, tile_position, 30, tile_color, tile_speed, None)
                new_tile.list_ref = tiles
                tiles.append(new_tile)
            if spawned:
                print(f"Beat spawn at t={current_time:.2f}s (kick={is_kick})")
        
        return spawned

def get_index_from_name(name, tiles):
    for i, tile in enumerate(tiles):
        if tile.name == name:
            return i
    return -1

def tile_generator(tiles, screen, spawn_count=0, spawn_pattern="sequential", lane_positions=None):
    """
    Spawn tiles in lanes with configurable patterns.
    
    Spawn patterns:
    - "sequential": 0→1→2→3→4→0 (left to right)
    - "random": Random lane each spawn
    - "alternating": 0→4→1→3→2 (outside to inside)
    - "center_first": 2→1→3→0→4 (center outward)
    - "zigzag": 0→2→4→3→1 (zigzag pattern)
    """
    if lane_positions is None:
        lane_positions = [screen.get_width() / 2 + (i - 2) * 150 for i in range(5)]
    
    screen_width = screen.get_width()
    
    # Determine which lane to spawn in based on pattern
    if spawn_pattern == "sequential":
        lane_index = spawn_count % 5
    elif spawn_pattern == "random":
        lane_index = random.randint(0, 4)
    elif spawn_pattern == "alternating":
        pattern_seq = [0, 4, 1, 3, 2]
        lane_index = pattern_seq[spawn_count % 5]
    elif spawn_pattern == "center_first":
        pattern_seq = [2, 1, 3, 0, 4]
        lane_index = pattern_seq[spawn_count % 5]
    elif spawn_pattern == "zigzag":
        pattern_seq = [0, 2, 4, 3, 1]
        lane_index = pattern_seq[spawn_count % 5]
    else:
        lane_index = spawn_count % 5
    
    # Spawn tile in the selected lane
    tile_position = pygame.math.Vector2(lane_positions[lane_index], -50)
    tile_color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)])
    tile_speed = random.randint(100, 110)
    
    # Create and add tile
    tile_name = f"tile_{spawn_count}"
    new_tile = GameObject(tile_name, tile_position, 30, tile_color, tile_speed, None)
    new_tile.list_ref = tiles
    tiles.append(new_tile)

def display_user_camera(screen):

    # Initialize tracker if not already done
    if not hasattr(display_user_camera, 'tracker'):
        display_user_camera.tracker = HandTracker()
    
    tracker = display_user_camera.tracker
    
    # Process frame: capture, detect, analyze, draw
    if not tracker.process_frame():
        return
    
    # Get processed frame from tracker
    frame = tracker.get_frame()
    if frame is None:
        return
    
    # Resize to match screen dimensions
    frame_resized = cv2.resize(frame, (screen.get_width(), screen.get_height()))
    
    # Convert OpenCV (BGR) frame to RGB for pygame
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    
    # Convert to pygame surface
    frame_surface = pygame.image.fromstring(
        frame_rgb.tobytes(),
        frame_rgb.shape[1::-1],
        'RGB'
    )
    
    # Blit camera feed to screen
    screen.blit(frame_surface, (0, 0))

def Start():
    #init
    
    score = 0
    pygame.init()  # Initialize all pygame modules including font
    screen = pygame.display.set_mode((1280, 720))  # Fixed resolution for better performance
    
    pygame.display.set_caption("Rhythm Game")
    clock = pygame.time.Clock()
    running = True
    dt = 0

    # Load and analyze music
    #print("[Game] Initializing audio...")
    #music_data = audio.analyze_audio(audio.AUDIO_FILE)
    #start_time = audio.play_audio(audio.AUDIO_FILE)
    #spawner = MusicSpawner(music_data['beat_times'], music_data['kick_times'], screen.get_width())
    #print(f"[Game] Ready! Game will spawn tiles based on {len(music_data['beat_times'])} beats")

    # objects 
    tiles = []

    # 5 catchers with equal spacing across screen
    lane_spacing = 100  # pixels between each catcher
    center_x = screen.get_width() / 2
    lane_positions = [center_x + (i - 2) * lane_spacing for i in range(5)]

    catchers = [
        GameObject(f"catcher_{i}", pygame.math.Vector2(lane_positions[i]-5, screen.get_height() - 100), 
                    40,
                    (255, 255, 255),
                    0,)
        for i in range(5)
    ]

    for catcher in catchers:
        catcher.list_ref = catchers
    
    # key_catcher_pairs = [
    #             (pygame.K_1, 0),
    #             (pygame.K_2, 1),
    #             (pygame.K_3, 2),
    #             (pygame.K_4, 3),
    #             (pygame.K_5, 4),
    #         ]
    
    gesture_catcher_pairs = [
                ("Closed_Fist", 0),
                ("Open_Palm", 1),
                ("Pointing_Up", 2),
                ("Thumb_Up", 3),
                ("Victory", 4),
            ]
    
    spawn_count = 0  # Track tile spawns for pattern rotation
    spawn_pattern = "alternating"  # CHOOSE PATTERN HERE: "sequential", "random", "alternating", "center_first", "zigzag"
    
    spawn_timer = 0  # Timer for tile spawning
    spawn_interval = 0.8  # Spawn a tile every 0.8 seconds (adjust this to change difficulty)

    font = pygame.font.Font(None, 36)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill("black")
        display_user_camera(screen)

        ## PRIMARY: POINTER COLLISION (Finger-based catching)
        keys = pygame.key.get_pressed()
        tiles_to_remove = []
        catcher_used_this_frame = set()  # Track which catchers were used
        catcher_caught_tiles_this_frame = set()  # Track which catchers caught tiles
        
        # Get gesture and finger position for both hands
        frame_dims = display_user_camera.tracker.get_frame_dimensions()
        
        # Hand 0
        get_gesture_name = display_user_camera.tracker.get_gesture_name(0)
        finger_pos = display_user_camera.tracker.get_finger_position(0, finger_index=8)  # Index finger
        
        finger_screen_pos = None
        if finger_pos and frame_dims:
            # Convert normalized finger position to screen coordinates
            finger_screen_x = finger_pos[0] * screen.get_width()
            finger_screen_y = finger_pos[1] * screen.get_height()
            finger_screen_pos = (finger_screen_x, finger_screen_y)
        
        # Hand 1 (second hand)
        finger_pos_hand1 = display_user_camera.tracker.get_finger_position(1, finger_index=8)  # Index finger
        finger_screen_pos_hand1 = None
        if finger_pos_hand1 and frame_dims:
            # Convert normalized finger position to screen coordinates
            finger_screen_x_h1 = finger_pos_hand1[0] * screen.get_width()
            finger_screen_y_h1 = finger_pos_hand1[1] * screen.get_height()
            finger_screen_pos_hand1 = (finger_screen_x_h1, finger_screen_y_h1)
        
        #Handle Open_Palm - activate all catchers simultaneously
        if get_gesture_name == "Open_Palm":
            for catcher in catchers:
                catcher.click_effect = 5  # Expand all catchers
                # delete the upcoming tiles if Open_Palm active
                for tile in tiles[:]:
                    if tile.position.y > screen.get_height() - 100:  # Only affect tiles close to catchers
                        if tile not in tiles_to_remove:
                            tiles_to_remove.append(tile)
                            score += 1
        
        # Pointer collision detection for Hand 0
        if finger_screen_pos:
            for i, catcher in enumerate(catchers):
                if catcher.point_collision(finger_screen_pos[0], finger_screen_pos[1], radius=40):
                    catcher.click_effect = 5  # Visual feedback
                    catcher_used_this_frame.add(i)  # Mark catcher as used
                    
                    for tile in tiles[:]:
                        if catcher.point_collision(tile.position.x + tile.size/2, tile.position.y + tile.size/2, radius=50):
                            if tile not in tiles_to_remove:
                                tiles_to_remove.append(tile)
                                catcher_caught_tiles_this_frame.add(i)  # Mark catcher caught tile
                                score += 1
        
        # Pointer collision detection for Hand 1 (second hand)
        if finger_screen_pos_hand1:
            for i, catcher in enumerate(catchers):
                if catcher.point_collision(finger_screen_pos_hand1[0], finger_screen_pos_hand1[1], radius=40):
                    catcher.click_effect = 5  # Visual feedback
                    catcher_used_this_frame.add(i)  # Mark catcher as used
                    
                    for tile in tiles[:]:
                        if catcher.point_collision(tile.position.x + tile.size/2, tile.position.y + tile.size/2, radius=50):
                            if tile not in tiles_to_remove:
                                tiles_to_remove.append(tile)
                                catcher_caught_tiles_this_frame.add(i)  # Mark catcher caught tile
                                score += 1
        
        # Gesture-based catching (SECONDARY - only if pointer didn't catch)
        # if not tiles_to_remove:
        #     for gesture_name, catcher_index in gesture_catcher_pairs:
        #         if gesture_name == get_gesture_name and gesture_name != "Open_Palm":
        #             catcher = catchers[catcher_index]
        #             catcher.click_effect = 5
                    
        #             for tile in tiles[:]:
        #                 if catcher.collision(tile) and tile not in tiles_to_remove:
        #                     tiles_to_remove.append(tile)
        #                     score += 1

        # Remove caught tiles
        for tile in tiles_to_remove:
            if tile in tiles:
                tile.delete()
        
        # Provide feedback for catcher actions
        for i, catcher in enumerate(catchers):
            if i in catcher_used_this_frame:
                if i in catcher_caught_tiles_this_frame:
                    # Caught tiles - show green feedback
                    catcher.feedback_color = (0, 255, 0)  # Green
                    catcher.feedback_timer = 0.3  # Show for 0.3 seconds
                else:
                    # Used but didn't catch - show red feedback and lose points
                    catcher.feedback_color = (255, 0, 0)  # Red
                    catcher.feedback_timer = 0.3  # Show for 0.3 seconds
                    score -= 1  # Lose a point for wrong action
        ##

        for tile in tiles:
            pygame.draw.rect(screen, tile.color, (tile.position.x, tile.position.y, tile.size, tile.size))
            tile.position.y += tile.speed * dt

        for catcher in catchers:
            display_size = catcher.get_display_size()
            # Center the expansion around the catcher
            offset = (display_size - catcher.size) / 2
            
            # Determine color: feedback color if active, otherwise original color
            if catcher.feedback_timer > 0:
                display_color = catcher.feedback_color
                catcher.feedback_timer -= dt
                if catcher.feedback_timer < 0:
                    catcher.feedback_timer = 0
            else:
                display_color = catcher.original_color
            
            pygame.draw.rect(screen, display_color, (catcher.position.x - offset, catcher.position.y - offset, display_size, display_size))
            # Decrement click effect
            if catcher.click_effect > 0:
                catcher.click_effect -= 1
        
        # Draw finger position indicator for both hands (circle crosshair)
        # Hand 0 pointer (cyan)
        if finger_screen_pos:
            # Draw circle at finger position
            pygame.draw.circle(screen, (0, 255, 255), (int(finger_screen_pos[0]), int(finger_screen_pos[1])), 15, 2)
            # Draw crosshair
            pygame.draw.line(screen, (0, 255, 255), 
                           (int(finger_screen_pos[0]) - 20, int(finger_screen_pos[1])), 
                           (int(finger_screen_pos[0]) + 20, int(finger_screen_pos[1])), 2)
            pygame.draw.line(screen, (0, 255, 255), 
                           (int(finger_screen_pos[0]), int(finger_screen_pos[1]) - 20), 
                           (int(finger_screen_pos[0]), int(finger_screen_pos[1]) + 20), 2)
        
        # Hand 1 pointer (magenta)
        if finger_screen_pos_hand1:
            # Draw circle at finger position
            pygame.draw.circle(screen, (255, 0, 255), (int(finger_screen_pos_hand1[0]), int(finger_screen_pos_hand1[1])), 15, 2)
            # Draw crosshair
            pygame.draw.line(screen, (255, 0, 255), 
                           (int(finger_screen_pos_hand1[0]) - 20, int(finger_screen_pos_hand1[1])), 
                           (int(finger_screen_pos_hand1[0]) + 20, int(finger_screen_pos_hand1[1])), 2)
            pygame.draw.line(screen, (255, 0, 255), 
                           (int(finger_screen_pos_hand1[0]), int(finger_screen_pos_hand1[1]) - 20), 
                           (int(finger_screen_pos_hand1[0]), int(finger_screen_pos_hand1[1]) + 20), 2)

        # Draw score on screen
        font = pygame.font.Font(None, 48)  # Default font, size 48
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))  # White text
        screen.blit(score_text, (10, 10))  # Top-left corner
        
        pygame.display.flip()
        dt = clock.tick(120) / 1000

        # Update spawn timer (non-blocking)
        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            tile_generator(tiles, screen, spawn_count, spawn_pattern, lane_positions)
            spawn_count += 1
            spawn_timer = 0  # Reset timer

        print(f"Score: {score}, FPS: {clock.get_fps():.0f}")

    pygame.quit()