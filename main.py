import mediapipe as mp
import cv2
import math
#https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
#https://docs.opencv.org/3.4/db/deb/tutorial_display_image.html
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

CANNED_GESTURE_OPTIONS = {
    "display_names_locale": "en",
    "max_results": -1,
    "score_threshold": 0.0,
    "category_allowlist": [],
    "category_denylist": [],
}

capture = cv2.VideoCapture(0)

def get_distance(LM1, LM2, w, h):
    x1, y1 = int(LM1.x * w), int(LM1.y * h)
    x2, y2 = int(LM2.x * w), int(LM2.y * h)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def get_points(LM1, LM2, w, h):
    x1, y1 = int(LM1.x * w), int(LM1.y * h)
    x2, y2 = int(LM2.x * w), int(LM2.y * h)
    return x1, y1, x2, y2

def normalized_distance(LM1, LM2):
    return math.sqrt((LM2.x - LM1.x) ** 2 + (LM2.y - LM1.y) ** 2)

def recognize_hand_gesture(hand_lms, options=None):
    options = options or CANNED_GESTURE_OPTIONS
    landmarks = hand_lms.landmark

    thumb_extended = normalized_distance(landmarks[4], landmarks[0]) > normalized_distance(landmarks[3], landmarks[0])
    index_extended = landmarks[8].y < landmarks[6].y
    middle_extended = landmarks[12].y < landmarks[10].y
    ring_extended = landmarks[16].y < landmarks[14].y
    pinky_extended = landmarks[20].y < landmarks[18].y

    gesture_name = "None"
    score = 1.0

    if not any([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]):
        gesture_name = "Closed_Fist"
    elif all([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended]):
        gesture_name = "Open_Palm"
    elif index_extended and not any([middle_extended, ring_extended, pinky_extended, thumb_extended]):
        gesture_name = "Pointing_Up"
    elif thumb_extended and not any([index_extended, middle_extended, ring_extended, pinky_extended]):
        if landmarks[4].y < landmarks[3].y:
            gesture_name = "Thumb_Up"
        elif landmarks[4].y > landmarks[3].y:
            gesture_name = "Thumb_Down"
    elif index_extended and middle_extended and not any([ring_extended, pinky_extended]):
        gesture_name = "Victory"
    elif thumb_extended and index_extended and pinky_extended and not any([middle_extended, ring_extended]):
        gesture_name = "ILoveYou"

    allowlist = set(options.get("category_allowlist", []))
    denylist = set(options.get("category_denylist", []))
    score_threshold = options.get("score_threshold", 0.0)

    if score < score_threshold:
        return "None", 0.0
    if allowlist and gesture_name not in allowlist:
        return "None", 0.0
    if denylist and gesture_name in denylist:
        return "None", 0.0

    return gesture_name, score

prev_wrist = None  


with mp_hands.Hands(min_detection_confidence=0.6, min_tracking_confidence=0.6) as hands:
    while capture.isOpened():
        ret, frame = capture.read()
        if(ret == False):
            break
        frame = cv2.flip(frame, 1) # numbers: 0: horizontal, 1: vertical, -1: both
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detected_image = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) 

        if detected_image.multi_hand_landmarks:
            for hand_lms in detected_image.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_lms,
                    mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                        color=(255, 0, 255), thickness=2, circle_radius=2),
                    connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                        color=(20, 180, 90), thickness=2, circle_radius=2)
                    )
                
                h,w,_ = image.shape

                #thumb tip is 4, index tip is 8, middle tip is 12, ring tip is 16, pinky tip is 20

                thumb = hand_lms.landmark[4]
                index = hand_lms.landmark[8]
                distante = get_distance(thumb, index, w, h)

                if distante < 30:
                    print("collision")
                    cv2.putText(image, "KIMBA", (200,200), cv2.FONT_HERSHEY_SIMPLEX,1, (0, 255, 0),2)

                gesture_name, gesture_score = recognize_hand_gesture(hand_lms, CANNED_GESTURE_OPTIONS)
                cv2.putText(image, f"Gesture: {gesture_name} ({gesture_score:.1f})", (50, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                
                #hand speed calculation
                wrist = hand_lms.landmark[0]
                wx, wy = int(wrist.x * w), int(wrist.y * h)
                if prev_wrist is not None:
                    speed = math.sqrt((wx - prev_wrist[0])**2 + (wy - prev_wrist[1])**2)
                    cv2.putText(image, f"Speed: {speed:.1f} px/frame", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                prev_wrist = (wx, wy)
                    
                cv2.circle(image, (int(hand_lms.landmark[4].x * w), int(hand_lms.landmark[4].y * h)), 10, (255, 0, 255), -1)
                cv2.circle(image, (int(hand_lms.landmark[8].x * w), int(hand_lms.landmark[8].y * h)), 10, (255, 0, 255), -1)
                
                    
        cv2.imshow('Webcam', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

capture.release()
cv2.destroyAllWindows()