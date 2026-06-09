from . import HelperFunctions as helpers


def _detect_extended_fingers(hand_landmarks):
    landmarks = hand_landmarks.landmark
    thumb_tip_dist = helpers.normalized_distance(landmarks[4], landmarks[0])
    thumb_ip_dist = helpers.normalized_distance(landmarks[3], landmarks[0])
    return {
        "thumb": thumb_tip_dist > thumb_ip_dist,
        "index": landmarks[8].y < landmarks[6].y,
        "middle": landmarks[12].y < landmarks[10].y,
        "ring": landmarks[16].y < landmarks[14].y,
        "pinky": landmarks[20].y < landmarks[18].y,
    }


def recognize_hand_gesture(hand_landmarks):
    fingers = _detect_extended_fingers(hand_landmarks)
    total = sum(fingers.values())

    if fingers["index"] and not any([
        fingers["thumb"], fingers["middle"], fingers["ring"], fingers["pinky"],
    ]):
        return "Pointing_Up"
    if fingers["thumb"] and not any([
        fingers["index"], fingers["middle"], fingers["ring"], fingers["pinky"],
    ]):
        return "Thumb_Up"
    if fingers["index"] and fingers["middle"] and not any([
        fingers["thumb"], fingers["ring"], fingers["pinky"],
    ]):
        return "Victory"
    if total == 5:
        return "Open_Palm"
    if total == 0:
        return "Closed_Fist"
    return "None"
