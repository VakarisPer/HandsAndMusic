import mediapipe as mp
import cv2
from . import HandGesture as hg


class HandTracker:
    def __init__(self, detection_confidence=0.5, tracking_confidence=0.5,
                 camera_width=320, camera_height=240,
                 model_complexity=0, draw_landmarks=True):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
        self._draw_landmarks_flag = draw_landmarks
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=model_complexity,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.current_frame = None
        self.hand_landmarks = []
        self.gesture_info = []

    def capture_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            return False
        frame = cv2.flip(frame, 1)
        self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return True

    def detect_hands(self):
        if self.current_frame is None:
            return False
        detected_image = self.hands.process(self.current_frame)
        self.current_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR)
        self.hand_landmarks = detected_image.multi_hand_landmarks or []
        return len(self.hand_landmarks) > 0

    def draw_landmarks(self):
        if self.current_frame is None or not self.hand_landmarks:
            return
        for hand_lms in self.hand_landmarks:
            self.mp_drawing.draw_landmarks(
                self.current_frame, hand_lms,
                self.mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                    color=(255, 0, 255), thickness=2, circle_radius=2),
                connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                    color=(20, 180, 90), thickness=2, circle_radius=2),
            )

    def analyze_gestures(self):
        if self.current_frame is None or not self.hand_landmarks:
            return
        self.gesture_info = []
        for hand_lms in self.hand_landmarks:
            gesture_name = hg.recognize_hand_gesture(hand_lms)
            self.gesture_info.append({
                'gesture': gesture_name,
                'landmarks': hand_lms,
            })

    def get_gesture_name(self, hand_index=0):
        if hand_index < len(self.gesture_info):
            return self.gesture_info[hand_index]['gesture']
        return None

    def get_finger_position(self, hand_index=0, finger_index=8):
        if hand_index < len(self.gesture_info):
            landmarks = self.gesture_info[hand_index]['landmarks']
            if landmarks and finger_index < len(landmarks.landmark):
                finger = landmarks.landmark[finger_index]
                return (finger.x, finger.y)
        return None

    def get_frame_dimensions(self):
        if self.current_frame is not None:
            h, w, _ = self.current_frame.shape
            return (w, h)
        return None

    def process_frame(self):
        if not self.capture_frame():
            return False
        self.detect_hands()
        if self._draw_landmarks_flag:
            self.draw_landmarks()
        self.analyze_gestures()
        return True

    def get_frame(self):
        return self.current_frame

    def release(self):
        self.capture.release()
        self.hands.close()


if __name__ == "__main__":
    tracker = HandTracker(draw_landmarks=True, model_complexity=0,
                          camera_width=640, camera_height=480)
    while tracker.capture.isOpened():
        if not tracker.process_frame():
            break
        cv2.imshow('Hand Tracking', tracker.get_frame())
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    tracker.release()
    cv2.destroyAllWindows()
