"""Input mapping system."""

import pygame


class InputSystem:
    """Maps gestures and keyboard keys into lane indices."""

    def __init__(self, gesture_map: dict[str, int]) -> None:
        self.gesture_map = gesture_map
        self.key_map = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
            pygame.K_5: 4,
        }

    def lanes_from_gestures(self, gestures: list[str]) -> set[int]:
        lanes = set()
        for gesture in gestures:
            lane = self.gesture_map.get(gesture)
            if lane is not None:
                lanes.add(lane)
        return lanes

    def lanes_from_keyboard(self) -> set[int]:
        keys = pygame.key.get_pressed()
        lanes = set()
        for key, lane in self.key_map.items():
            if keys[key]:
                lanes.add(lane)
        return lanes

