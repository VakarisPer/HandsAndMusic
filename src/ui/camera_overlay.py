"""Camera overlay helpers for the menu/UI layer."""

import cv2
import pygame
from hand_tracking.Tracking import HandTracker
from src.config.settings import (
    HAND_CAMERA_HEIGHT,
    HAND_CAMERA_WIDTH,
    HAND_DETECTION_CONFIDENCE,
    HAND_MODEL_COMPLEXITY,
    HAND_TRACKING_CONFIDENCE,
)


def display_user_camera(screen):
    if not hasattr(display_user_camera, 'tracker') \
            or display_user_camera.tracker is None:
        display_user_camera.tracker = HandTracker(
            detection_confidence=HAND_DETECTION_CONFIDENCE,
            tracking_confidence=HAND_TRACKING_CONFIDENCE,
            camera_width=HAND_CAMERA_WIDTH,
            camera_height=HAND_CAMERA_HEIGHT,
            model_complexity=HAND_MODEL_COMPLEXITY,
            draw_landmarks=True,
        )

    tracker = display_user_camera.tracker

    if not tracker.process_frame():
        return

    frame = tracker.get_frame()
    if frame is None:
        return

    frame_resized = cv2.resize(frame, (screen.get_width(), screen.get_height()))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.image.fromstring(
        frame_rgb.tobytes(),
        frame_rgb.shape[1::-1],
        'RGB',
    )
    screen.blit(frame_surface, (0, 0))


def release_camera_tracker():
    """Release the menu's shared camera tracker (if it was created)."""
    if getattr(display_user_camera, 'tracker', None):
        display_user_camera.tracker.release()
        display_user_camera.tracker = None


def draw_finger_indicators(screen, hand0_pos, hand1_pos):
    for pos, color in [(hand0_pos, (0, 255, 255)), (hand1_pos, (255, 0, 255))]:
        if pos:
            pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), 15, 2)
            pygame.draw.line(screen, color, (int(pos[0]) - 20, int(pos[1])), (int(pos[0]) + 20, int(pos[1])), 2)
            pygame.draw.line(screen, color, (int(pos[0]), int(pos[1]) - 20), (int(pos[0]), int(pos[1]) + 20), 2)


def to_screen_coordinates(finger_pos, screen):
    if finger_pos is None:
        return None
    return (finger_pos[0] * screen.get_width(), finger_pos[1] * screen.get_height())
