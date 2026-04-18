import HelperFunctions as help

CANNED_GESTURE_OPTIONS = {
    "display_names_locale": "en",
    "max_results": -1,
    "score_threshold": 0.0,
    "category_allowlist": [],
    "category_denylist": [],
}

def recognize_hand_gesture(hand_lms, options=None):
    options = options or CANNED_GESTURE_OPTIONS
    landmarks = hand_lms.landmark

    thumb_extended = help.get_normalized_distance(landmarks[4], landmarks[0]) > help.get_normalized_distance(landmarks[3], landmarks[0])
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

