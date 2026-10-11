import numpy as np
from regions.region import Region
from borders.border import Border
from scipy.sparse import coo_array
from scipy.spatial import KDTree
# from scipy.interpolate import CloughTocher2DInterpolator
from scipy.interpolate import LinearNDInterpolator
from image.mesh import DATA_TYPE_COLORED_VERTEX
from util.inspection_utils import *
from util.rasterize import *


def get_region_center(region: Region):
    region_borders = np.unique(np.concat([border.full_points for border in region.total_borders], axis=1), axis=1)

    border_tree = KDTree(region_borders.T)
    border_matches = border_tree.query(region.points.T)
    border_distances = border_matches[0]
    max_distance = np.max(border_distances)
    middle_indices = np.flatnonzero(np.equal(border_distances, max_distance))
    return region.points[:, middle_indices]


def fix_out_of_bounds(vertex_colors, vertex_coords, region_borders, border_values):
    """Integer rounding errors may cause some vertices to lie slightly out of the region.
    If so, just pick the color of the closest border vertex"""
    out_of_bounds = np.isnan(vertex_colors)
    if out_of_bounds.any():
        border_tree = KDTree(region_borders.T)
        out_of_bounds_coords = vertex_coords[:, out_of_bounds]
        border_matches = border_tree.query(out_of_bounds_coords.T)
        closest_border_values = border_values[border_matches[1]]
        vertex_colors[out_of_bounds] = closest_border_values


def get_border_value(border: Border, region: Region):
    if border.region_one.id == region.id:
        bordering_region = border.region_two
    else:
        bordering_region = border.region_one
    if bordering_region.is_void:
        return region.value
    else:
        return (region.value + bordering_region.value) // 2


def color_vertices(regions: list[Region]):
    opaque_regions = [region for region in regions if not region.is_void and len(region.polygons) > 0]
    polygon_vertices = np.unique(
        np.concat(
            [polygon for region in opaque_regions for polygon in region.polygons], axis=1
        ), axis=1
    )
    colored_vertices = np.zeros([polygon_vertices.shape[1]], dtype=DATA_TYPE_COLORED_VERTEX)
    colored_vertices['y'] = polygon_vertices[0]
    colored_vertices['x'] = polygon_vertices[1]
    color_value_accumulator = np.zeros(polygon_vertices.shape[1], dtype=np.float32)
    color_value_count = np.zeros(polygon_vertices.shape[1], dtype=np.float32)
    vertex_index_map = coo_array(
        (np.arange(polygon_vertices.shape[1]), polygon_vertices),
        shape=np.max(polygon_vertices, axis=1) + 1
    )
    for region in opaque_regions:
        border_points, original_index_into = np.unique(
            np.concat([border.decomposed_points for border in region.total_borders], axis=1),
            axis=1, return_inverse=True
        )
        point_accumulated_value = np.zeros(border_points.shape[1], dtype=np.float64)
        point_occurrence_count = np.zeros(border_points.shape[1], dtype=np.int32)
        offset = 0
        any_border_above = False
        any_border_below = False
        for border in region.total_borders:
            border_value = get_border_value(border, region)
            point_indices = original_index_into[offset:offset+border.decomposed_points.shape[1]]
            point_accumulated_value[point_indices] += border_value
            point_occurrence_count[point_indices] += 1
            offset += border.decomposed_points.shape[1]
            any_border_above = any_border_above or border_value >= region.value
            any_border_below = any_border_below or border_value <= region.value
        if any_border_above and any_border_below:
            middles = np.zeros([2, 0], dtype=np.int32)
        else:
            middles = get_region_center(region)

        border_values = np.divide(point_accumulated_value, point_occurrence_count)
        interpolation_points = np.concat([border_points, middles], axis=1)
        interpolation_values = np.concat([
            border_values,
            np.full([middles.shape[1]], region.value)
        ])
        # interpolator = CloughTocher2DInterpolator(interpolation_points.T, interpolation_values)
        interpolator = LinearNDInterpolator(interpolation_points.T, interpolation_values)
        region_vertices = np.unique(
            np.concat(region.polygons, axis=1), axis=1
        )
        vertex_color = interpolator(region_vertices.T)
        fix_out_of_bounds(vertex_color, region_vertices, border_points, border_values)
        vertex_indices = vertex_index_map[*region_vertices].toarray()
        new_colors = (vertex_color / 255.0).astype(np.float32)
        color_value_accumulator[vertex_indices] += new_colors
        color_value_count[vertex_indices] += 1
    color_values = color_value_accumulator / color_value_count
    colored_vertices['color'] = np.clip(color_values, 0.0, 1.0)
    return colored_vertices



