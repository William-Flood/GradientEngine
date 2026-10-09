import numpy as np
from borders.border import Border
from util.inspection_utils import *


def get_masks(points):
    AB = [
        points[0, -1] - points[0, 0],
        points[1, -1] - points[1, 0]
    ]

    BE = [
        points[0] - points[0, -1],
        points[1] - points[1, -1]
    ]

    AE = [
        points[0] - points[0, 0],
        points[1] - points[1, 0]
    ]

    return np.less(np.dot(AB, BE), 0), np.greater(np.dot(AB, AE), 0)


def get_unguarded_distances_from_segment(points):
    a = points[0, -1] - points[0, 0]
    b = points[1, -1] - points[1, 0]
    c = points[1, -1] * points[0, 0] - points[0, -1] * points[1, 0]
    return np.abs(points[1] * a - points[0] * b + c) / np.linalg.norm(points[:, -1] - points[:, 0])


def get_distances_from_segment(points):
    before_end_mask, after_start_mask = get_masks(points)
    masked_distances_from_line = np.multiply(
        np.multiply(after_start_mask, before_end_mask),
        get_unguarded_distances_from_segment(points)
    )
    masked_distances_from_start = np.multiply(
        np.linalg.norm(points - points[:, [0]], axis=0),
        np.logical_not(after_start_mask)
    )
    masked_distances_from_end = np.multiply(
        np.linalg.norm(points - points[:, [-1]], axis=0),
        np.logical_not(before_end_mask)
    )
    return masked_distances_from_line + masked_distances_from_start + masked_distances_from_end


def ramer_douglas_peucker(points, distance_threshold, min_length):
    if points.shape[1] < 3:
        return np.arange(points.shape[1])
    distances = get_distances_from_segment(points)
    max_distance_index = np.argmax(distances)
    if max_distance_index < min_length:
        if points.shape[1] > points.shape[1] * 2:
            max_distance_index = min_length
        else:
            max_distance_index = points.shape[1] // 2
    elif max_distance_index > points.shape[1] - 1 - min_length:
        if points.shape[1] > points.shape[1] * 2:
            max_distance_index = points.shape[1] - 1 - min_length
        else:
            max_distance_index = points.shape[1] // 2
    if distances[max_distance_index] > distance_threshold:
        lower_indices = ramer_douglas_peucker(points[:, :max_distance_index], distance_threshold, min_length)[:-1]
        upper_indices = ramer_douglas_peucker(
            points[:, max_distance_index:],
            distance_threshold,
            min_length)[1:] + max_distance_index
        return np.concat([
            lower_indices,
            [max_distance_index],
            upper_indices
        ])
    else:
        return np.array([0, points.shape[1] - 1])


def decimate(border: Border, distance_threshold, min_length):
    decomposition_indices = ramer_douglas_peucker(border.full_points, distance_threshold, min_length)
    border_decomposed_points = border.full_points[:, decomposition_indices]
    border.decomposed_points = border_decomposed_points