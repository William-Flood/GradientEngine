from gradengrs import smooth_polygons
from regions.region import Region
import numpy as np
from util.inspection_utils import test_region
from util.rasterize import rasterize_polygon

def smooth_region_polygons(regions: list[Region], mesh_smooth_convergence_ratio):
    for region in regions:
        region_polygons = []
        for polygon in region.polygons:
            if polygon.shape[1] > 2 and np.equal(np.unique(polygon, axis=1, return_counts=True)[1], 1).all():
                region_polygons.append(polygon)
        rust_cut_input = f"vec![\n  {",\n  ".join(f"vec![{", ".join(f"({p[0]}, {p[1]})" for p in polygon.T)}]" for polygon in region_polygons)}\n]"
        smooth_results = smooth_polygons(region_polygons, mesh_smooth_convergence_ratio)
        region.polygons = [result.points for result in smooth_results]