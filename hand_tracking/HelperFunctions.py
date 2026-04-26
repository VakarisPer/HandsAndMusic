import math

def get_pixel_distance(LM1, LM2, w, h):
    x1, y1 = int(LM1.x * w), int(LM1.y * h)
    x2, y2 = int(LM2.x * w), int(LM2.y * h)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def get_points(LM1, LM2, w, h):
    x1, y1 = int(LM1.x * w), int(LM1.y * h)
    x2, y2 = int(LM2.x * w), int(LM2.y * h)
    return x1, y1, x2, y2

# for hand_gesture to have the best predictions
def get_normalized_distance(LM1, LM2):
    return math.sqrt((LM2.x - LM1.x) ** 2 + (LM2.y - LM1.y) ** 2)

