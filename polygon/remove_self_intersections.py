import numpy as np
from regions.region import Region
from gradengrs import remove_intersecting_edges
from util.inspection_utils import *
from util.rasterize import rasterize_polygon, rasterize_line
from util.inspection_utils_gui import *


def remove_self_intersections(regions: list[Region]):
    for region in regions:
        region_polygons = []
        for polygon in region.polygons:
            if polygon.shape[1] > 2 and np.equal(np.unique(polygon, axis=1, return_counts=True)[1], 1).all():
                region_polygons.append(polygon)
        rust_cut_input = f"vec![\n  {",\n  ".join(f"vec![{", ".join(f"({p[0]}, {p[1]})" for p in polygon.T)}]" for polygon in region_polygons)}\n]"
        scale = 20
        def inspect_polys(ids):
            polys = [poly for pid, poly in enumerate(region_polygons) if pid in ids]
            polycoords = np.concat(polys, axis=1)
            min_poly = np.min(polycoords, axis=1)
            max_poly = np.max(polycoords, axis=1)
            polyedges = np.concat([rasterize_polygon(poly * scale) for poly in polys], axis=1) - min_poly[:, np.newaxis] * scale
            test_region((max_poly - min_poly) * scale + 1, polyedges)
        def inspect_edges(point_list):
            lines = []
            for i in range(len(point_list) - 1):
                lines.append(rasterize_line(np.array(point_list[i]) * scale, np.array(point_list[i + 1]) * scale))
            combined = np.concat(lines, axis=1)
            min_lines = np.min(combined, axis=1)
            max_lines = np.max(combined, axis=1)
            combined_adjusted = combined - min_lines[:, np.newaxis]
            test_region((max_lines - min_lines) + 1, combined_adjusted)
        def inspect_poly_verts(point_list):
            combined = np.concat([region_polygons[pid] for pid in point_list], axis=1)
            min_verts = np.min(combined, axis=1)
            max_verts = np.max(combined, axis=1)
            combined_adjusted = combined - min_verts[:, np.newaxis]
            test_region((max_verts - min_verts) + 1, combined_adjusted)
        def compare_poly_verts(point_lists):
            combined = np.stack([point for point_list in point_lists for point in point_list], axis=1)
            min_verts = np.min(combined, axis=1) * scale
            max_verts = np.max(combined, axis=1) * scale
            combined_adjusted = combined - min_verts[:, np.newaxis]
            for point_list in point_lists:
                adjusted_list = np.array(point_list).T * scale - min_verts[:, np.newaxis]
                test_region((max_verts - min_verts) + 1, adjusted_list)
        def inspect_intersection(y1, y2, y3, y4, x1, x2, x3, x4):
            lines = []
            lines.append(rasterize_line((y1, x1), (y2, x2)))
            lines.append(rasterize_line((y3, x3), (y4, x4)))
            combined = np.concat(lines, axis=1)
            min_lines = np.min(combined, axis=1)
            max_lines = np.max(combined, axis=1)
            combined_adjusted = combined - min_lines[:, np.newaxis]
            test_region((max_lines - min_lines) + 1, combined_adjusted)
        def inspect_point_list(point_lists):
            visualize_point_list(np.array(point_lists).T, np.arange(len(point_lists)))
        # inspect_verts([[321, 548], [313, 356], [328, 536], [332, 615], [326, 581]])
        # inspect_edges(368, 366, 371, 385, 629, 612, 664, 595)
        # print(f"Sanitizing {region.id}")
        sanitized_polygons = remove_intersecting_edges(region_polygons)
        region.polygons = [result.points for result in sanitized_polygons]
        # if region.id == 15:
        #     inspect_polys([23, 24])