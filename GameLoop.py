import pygame
import random

class GameObject:
    def __init__ (self, postion, size, color, speed):
        self.position = postion
        self.size = size
        self.color = color
        self.speed = speed


def Start():
    #init
    pygame.display.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Rhythm Game")
    clock = pygame.time.Clock()
    running = True
    dt = 0

    # objects 
    tiles = [
        GameObject(pygame.math.Vector2((screen.get_width() / 2) + (x * 50), (screen.get_height() / 2) + (y * 50)), 
                    30,
                    random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]),
                     random.randint(100, 300))

        for x in range(5)
        for y in range(1)
    ]

    cathers = [
        GameObject(pygame.math.Vector2((screen.get_width() / 2) + (x * 50), (screen.get_height() / 2) + (y * 50) + 300), 
                    30,
                    (255, 0, 255),
                     0)

        for x in range(5)
        for y in range(1)
    ]
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill("black")

        for tile in tiles:
            pygame.draw.rect(screen, tile.color, (tile.position.x, tile.position.y, tile.size, tile.size))
            tile.position.y += tile.speed * dt

        for cather in cathers:
            pygame.draw.rect(screen, cather.color, (cather.position.x, cather.position.y, cather.size, cather.size))

        pygame.display.flip()
        dt = clock.tick(60) / 1000

    pygame.quit()

