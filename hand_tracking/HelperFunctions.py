from math import sqrt


def pixel_distance(landmark_a, landmark_b, image_width, image_height):
    x1, y1 = int(landmark_a.x * image_width), int(landmark_a.y * image_height)
    x2, y2 = int(landmark_b.x * image_width), int(landmark_b.y * image_height)
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def normalized_distance(landmark_a, landmark_b):
    return sqrt((landmark_b.x - landmark_a.x) ** 2
                + (landmark_b.y - landmark_a.y) ** 2)
