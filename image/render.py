import numpy as np
from image.mesh import Mesh
from image.point_coloring import color_vertices
from image.renderer import Renderer
from regions.region import Region
from image.MakeOffscreenContext import CreateWindowA, CreateContext, DeleteContext
from image.buffers import CreateBuffers, ReadColorBuffer, DeleteBuffers
from PIL import Image
from win32con import *

def get_polygon_indices(regions: list[Region]):
    opaque_regions = [region for region in regions if not region.is_void]
    assert all(polygon.shape[1] == 4 for region in opaque_regions for polygon in region.polygons)
    _, polygon_indices = np.unique(
        np.concat([polygon for region in opaque_regions for polygon in region.polygons], axis=1), axis=1,
        return_inverse=True
    )
    rect_index_pattern = np.array([[0, 1, 2, 0, 2, 3]])
    polygon_meta_indexes_matrix = np.reshape(
        np.arange(np.sum([len(region.polygons) for region in regions])),
        [-1, 1]
    ) * 4 + rect_index_pattern
    polygon_meta_indexes = polygon_meta_indexes_matrix.flatten()
    return polygon_indices[polygon_meta_indexes].astype(np.uint32)

def render(regions: list[Region], image_size, output_file, stripes=255):
    height = image_size[0]
    width = image_size[1]
    hWnd = CreateWindowA(style=WS_POPUP, size=(width, height))
    CreateContext(hWnd)
    buffers = CreateBuffers(width, height)
    colored_vertices = color_vertices(regions)
    colored_vertices['y'] = 2 * (colored_vertices['y'] - image_size[0] / 2) / image_size[0]
    colored_vertices['x'] = 2 * (colored_vertices['x'] - image_size[1] / 2) / image_size[1]

    mesh_indices = get_polygon_indices(regions)
    region_mesh = Mesh().builds_quads(colored_vertices, mesh_indices)
    renderer = Renderer(region_mesh)
    renderer.draw()

    data, width, height = ReadColorBuffer(buffers)
    image = Image.frombytes("RGBA", (width, height), data)
    if stripes != 255:
        image_array = np.array(image)
        pixels_flattened = np.reshape(image_array, [-1, 4])
        non_transparent_indices = np.flatnonzero(np.equal(pixels_flattened[:, 3], 255))
        non_transparent = pixels_flattened[non_transparent_indices]
        original_values, original_indexes_into, counts = np.unique(
            non_transparent, axis=0, return_inverse=True, return_counts=True
        )
        stripe_histogram_size = non_transparent.shape[0] // stripes
        stripe_accumulator = 0
        stripe_values = np.zeros([original_values.shape[0], 4], dtype=np.uint8)
        current_stripe = 0
        stripe_index = 0
        for original_index in range(original_values.shape[0]):
            stripe_accumulator += counts[original_index]
            if stripe_accumulator > stripe_histogram_size:
                if stripe_index < (stripes - 2):
                    current_stripe = original_index
                    stripe_index += 1
                elif stripe_index == (stripes - 2):
                    current_stripe = original_values.shape[0] - 1
                    stripe_index += 1
                stripe_accumulator -= stripe_histogram_size
            stripe_values[original_index] = original_values[current_stripe]
        striped_nontransparent_values = stripe_values[original_indexes_into]
        pixels_flattened[non_transparent_indices] = striped_nontransparent_values
        image = Image.fromarray(np.reshape(pixels_flattened, [*image_size, 4]))



    image.save(output_file, "PNG")

    DeleteBuffers(buffers)
    DeleteContext()
