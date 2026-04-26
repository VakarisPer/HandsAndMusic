"""Hand-landmark math helpers."""

import math


def get_pixel_distance(lm1, lm2, w, h):
    x1, y1 = int(lm1.x * w), int(lm1.y * h)
    x2, y2 = int(lm2.x * w), int(lm2.y * h)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def get_points(lm1, lm2, w, h):
    x1, y1 = int(lm1.x * w), int(lm1.y * h)
    x2, y2 = int(lm2.x * w), int(lm2.y * h)
    return x1, y1, x2, y2


def get_normalized_distance(lm1, lm2):
    return math.sqrt((lm2.x - lm1.x) ** 2 + (lm2.y - lm1.y) ** 2)
