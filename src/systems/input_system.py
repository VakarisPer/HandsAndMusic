"""Input mapping system."""

import pygame


class InputSystem:
    """Maps keyboard keys into lane indices."""

    def __init__(self) -> None:
        self.key_map = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
            pygame.K_5: 4,
        }

    def lanes_from_keyboard(self) -> set[int]:
        keys = pygame.key.get_pressed()
        lanes = set()
        for key, lane in self.key_map.items():
            if keys[key]:
                lanes.add(lane)
        return lanes

