import gradengrs
from regions.region import Region
import numpy as np
from collections import defaultdict

def decimate_mesh(regions: list[Region], keep_length):
    polygon_list = []
    polygon_region_list = []
    non_transparent_regions = [region for region in regions if region.value != -1]
    for region in non_transparent_regions:
        for polygon in region.polygons:
            if polygon.shape[1] > 2 and np.equal(np.unique(polygon, axis=1, return_counts=True)[1], 1).all():
                polygon_list.append(polygon)
                polygon_region_list.append(region.id)
    rust_cut_input = f"vec![\n  {",\n  ".join(f"vec![{", ".join(f"({p[0]}, {p[1]})" for p in polygon.T)}]" for polygon in polygon_list)}\n]"
    cut_results = gradengrs.decimate_mesh(polygon_list, keep_length)
    new_region_polygon_matcher = defaultdict(list)
    for cut_result in cut_results:
        new_region_polygon_matcher[polygon_region_list[cut_result.original_id]].append(cut_result.points)
    for region in non_transparent_regions:
        region.polygons = new_region_polygon_matcher[region.id]