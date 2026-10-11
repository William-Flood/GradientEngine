from gradengrs import get_double_borders_dict
from PIL import Image
import numpy as np

def collect_border_points(image_shape, regions_array, values_array, mask_file_name):
    if mask_file_name is None:
        border_mask = np.zeros(image_shape, dtype=bool)
    else:
        border_mask = np.greater(np.array(Image.open(mask_file_name))[..., 3], 0)
    border_dict = get_double_borders_dict(image_shape, regions_array, values_array, border_mask)
    return border_dict
