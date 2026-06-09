"""Adapter for hand tracking provider."""

import warnings
from hand_tracking.Tracking import HandTracker

warnings.filterwarnings(
    "ignore",
    message=r"SymbolDatabase.GetPrototype\(\) is deprecated.*",
)


class HandTrackerAdapter:
    """Normalizes existing tracker output for the InputSystem."""

    def __init__(self) -> None:
        self._tracker = HandTracker()

    def poll_gestures(self) -> list[str]:
        if not self._tracker.process_frame():
            return []
        gestures: list[str] = []
        for hand_index in range(2):
            gesture = self._tracker.get_gesture_name(hand_index)
            if gesture:
                gestures.append(gesture)
        return gestures

    def poll_snapshot(self) -> tuple[list[str], list[tuple[float, float]]]:
        """Return current gesture names and normalized index-finger positions."""
        gestures = self.poll_gestures()
        points: list[tuple[float, float]] = []
        for hand_index in range(2):
            finger = self._tracker.get_finger_position(hand_index, finger_index=8)
            if finger:
                points.append((float(finger[0]), float(finger[1])))
        return gestures, points

    def get_frame(self):
        return self._tracker.get_frame()

    def shutdown(self) -> None:
        self._tracker.release()

