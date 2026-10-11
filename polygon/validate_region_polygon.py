import numpy as np
from regions.region import Region
from PIL import Image
from polygon.mesh import Mesh
from util.rasterize import rasterize_line

def validate_region_polygons(
        regions: list[Region],
        image_shape,
        validation_highlight_file_name="validation_failures.png"):
    invalid_list = []
    region_with_polygons = [region for region in regions if len(region.polygons) > 0]
    for region in region_with_polygons:
        region_border_points = region.polygons[0]
        if region_border_points.shape[1] < 3:
            invalid_list.append(region.points)
        else:
            _, unique_counts = np.unique(region_border_points, axis=1, return_counts=True)
            if np.greater(unique_counts, 1).any():
                invalid_list.append(region.points)
    if 0 < len(invalid_list):
        invalid_map = np.zeros([*image_shape, 4], dtype=np.uint8)
        for region_points in invalid_list:
            invalid_map[*region_points] = [255, 0, 0, 255]
        Image.fromarray(invalid_map).save(validation_highlight_file_name)
        raise Exception(f"Invalid image geometry detected - region borders collapsed. Validation issues highlighted in {validation_highlight_file_name}")
