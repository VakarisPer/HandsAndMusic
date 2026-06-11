"""Adapter for hand tracking provider."""

import warnings
from hand_tracking.Tracking import HandTracker
from src.config.settings import (
    HAND_CAMERA_HEIGHT,
    HAND_CAMERA_WIDTH,
    HAND_DETECTION_CONFIDENCE,
    HAND_MODEL_COMPLEXITY,
    HAND_TRACKING_CONFIDENCE,
)

warnings.filterwarnings(
    "ignore",
    message=r"SymbolDatabase.GetPrototype\(\) is deprecated.*",
)

_EMA_WEIGHT = 0.4
_DEBOUNCE_FRAMES = 3


class HandTrackerAdapter:
    """Normalizes existing tracker output for the InputSystem."""

    def __init__(self) -> None:
        self._tracker = HandTracker(
            detection_confidence=HAND_DETECTION_CONFIDENCE,
            tracking_confidence=HAND_TRACKING_CONFIDENCE,
            camera_width=HAND_CAMERA_WIDTH,
            camera_height=HAND_CAMERA_HEIGHT,
            model_complexity=HAND_MODEL_COMPLEXITY,
            draw_landmarks=True,
        )
        self._prev_positions: dict[int, tuple[float, float]] = {}
        self._gesture_streak: dict[int, tuple[str, int]] = {}
        self._stable_gestures: dict[int, str] = {}

    def _smooth(self, hand_index: int,
                raw: tuple[float, float]) -> tuple[float, float]:
        if hand_index in self._prev_positions:
            px, py = self._prev_positions[hand_index]
            sx = px + _EMA_WEIGHT * (raw[0] - px)
            sy = py + _EMA_WEIGHT * (raw[1] - py)
            smoothed = (sx, sy)
        else:
            smoothed = raw
        self._prev_positions[hand_index] = smoothed
        return smoothed

    def _debounce_gesture(self, hand_index: int, raw_gesture: str) -> str:
        prev_gesture, prev_count = self._gesture_streak.get(
            hand_index, ("None", 0))
        if raw_gesture == prev_gesture:
            count = prev_count + 1
        else:
            count = 1
        self._gesture_streak[hand_index] = (raw_gesture, count)
        if count >= _DEBOUNCE_FRAMES:
            self._stable_gestures[hand_index] = raw_gesture
            return raw_gesture
        return self._stable_gestures.get(hand_index, "None")

    def poll_gestures(self) -> list[str]:
        if not self._tracker.process_frame():
            return []
        gestures: list[str] = []
        for hand_index in range(2):
            raw = self._tracker.get_gesture_name(hand_index)
            if raw:
                gesture = self._debounce_gesture(hand_index, raw)
                gestures.append(gesture)
        return gestures

    def poll_snapshot(self) -> tuple[list[str], list[tuple[float, float]]]:
        """Return current gesture names and smoothed index-finger positions."""
        gestures = self.poll_gestures()
        points: list[tuple[float, float]] = []
        for hand_index in range(2):
            finger = self._tracker.get_finger_position(
                hand_index, finger_index=8)
            if finger:
                smoothed = self._smooth(
                    hand_index, (float(finger[0]), float(finger[1])))
                points.append(smoothed)
        return gestures, points

    def get_frame(self):
        return self._tracker.get_frame()

    def shutdown(self) -> None:
        self._tracker.release()

