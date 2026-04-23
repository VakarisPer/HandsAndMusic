from matplotlib.pylab import tile
import pygame
import random
import audio

tile_id = 0  # global counter


class GameObject:
    def __init__(self, name, position, size, color, speed, list_ref=None):
        self.name = name
        self.position = position
        self.size = size
        self.color = color
        self.speed = speed
        self.list_ref = list_ref  # Reference to the shared list

    def delete(self):
        self.list_ref.remove(self)  # Removes itself from the list
    
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
                x = random.randint(0, 4)
                tile_name = f"tile_{x}_{self.beat_index}"
                tile_position = pygame.math.Vector2((self.screen_width / 2) + (x * 50), -50)
                
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

def tile_generator(tiles, screen_width):
    x = random.randint(0, 4)
    tile_name = f"tile_{x}"
    tile_position = pygame.math.Vector2((screen_width / 2) + (x * 50), -50)
    tile_color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)])
    tile_speed = random.randint(100, 110)
    new_tile = GameObject(tile_name, tile_position, 30, tile_color, tile_speed, None)
    new_tile.list_ref = tiles
    print(f"Spawned: {tile_name}")
    tiles.append(new_tile)



def Start():
    #init
    score = 0
    pygame.display.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Rhythm Game")
    clock = pygame.time.Clock()
    running = True
    dt = 0

    # Load and analyze music
    print("[Game] Initializing audio...")
    music_data = audio.analyze_audio(audio.AUDIO_FILE)
    start_time = audio.play_audio(audio.AUDIO_FILE)
    spawner = MusicSpawner(music_data['beat_times'], music_data['kick_times'], screen.get_width())
    print(f"[Game] Ready! Game will spawn tiles based on {len(music_data['beat_times'])} beats")

    # objects 
    tiles = [
        #spawns 5 on start()
        GameObject(f"tile_{x}", pygame.math.Vector2(
                    (
                    screen.get_width() / 2) + (x * 50), (screen.get_height() / 2) + (y * 50)), 
                    30,
                    random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]),
                    random.randint(100, 110),
                      None)
        for x in range(5)
        for y in range(1)
    ]
    for tile in tiles:
        tile.list_ref = tiles

    cathers = [
        GameObject(f"cather_{x}_{y}", pygame.math.Vector2((screen.get_width() / 2) + (x * 50), (screen.get_height() / 2) + (y * 50) + 300), 
                    30,
                    (255, 0, 255),
                     0,)
        for x in range(5)
        for y in range(1)
    ]
    for cather in cathers:
        cather.list_ref = cathers
    
    key_catcher_pairs = [
                (pygame.K_1, 0),
                (pygame.K_2, 1),
                (pygame.K_3, 2),
                (pygame.K_4, 3),
                (pygame.K_5, 4),
            ]

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill("black")

        ## handle input
        keys = pygame.key.get_pressed()
        tiles_to_remove = []

        # Piano tiles style - 1-5 keys for each lane
        for key, catcher_index in key_catcher_pairs:
            if keys[key]:
                catcher = cathers[catcher_index]
                for tile in tiles[:]:  # Iterate over a copy
                    if catcher.collision(tile) and tile not in tiles_to_remove:
                        tiles_to_remove.append(tile)
                        score += 1

        # Remove caught tiles
        for tile in tiles_to_remove:
            if tile in tiles:
                tiles.remove(tile)
        ##

        for tile in tiles:
            pygame.draw.rect(screen, tile.color, (tile.position.x, tile.position.y, tile.size, tile.size))
            tile.position.y += tile.speed * dt

        for cather in cathers:
            pygame.draw.rect(screen, cather.color, (cather.position.x, cather.position.y, cather.size, cather.size))

        pygame.display.flip()
        dt = clock.tick(60) / 1000

        # Spawn tiles based on music beats
        current_time = audio.get_current_time(start_time)
        spawner.spawn_tiles(tiles, current_time)

        print(f"Score: {score}")

    pygame.quit()
