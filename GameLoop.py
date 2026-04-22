from matplotlib.pylab import tile
import pygame
import random

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

        # spawn in intervals
        if random.random() < 0.02:  # Adjust the spawn rate as needed  
            tile_generator(tiles, screen.get_width())

        print(f"Score: {score}")

    pygame.quit()
