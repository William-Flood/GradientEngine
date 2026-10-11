import numpy as np
from regions.region import Region
from gradengrs import remove_intersecting_edges
from util.inspection_utils import *
from util.rasterize import rasterize_polygon, rasterize_line
from util.inspection_utils_gui import *
from polygon.mesh import Mesh
from scipy.sparse.csgraph import depth_first_order


def cross_region_pass(regions: list[Region]):
    non_transparent_regions = [region for region in regions if region.value != -1]
    if len(non_transparent_regions) == 0:
        return
    polygon_list = [polygon for region in non_transparent_regions for polygon in region.polygons]
    polygon_regions = np.concat(
        [[nontransparent_region_index] * len(region.polygons)
            for nontransparent_region_index, region in enumerate(non_transparent_regions)
        ]
    )
    region_polygon_index = np.concat(
        [np.arange(len(region.polygons)) for region in non_transparent_regions])
    polygon_mesh = Mesh(polygon_list)
    unique_polygon_edges, edge_occurrences, edge_counts = np.unique(polygon_mesh.edge_index_and_polygon[0],
                                                                   return_counts=True, return_inverse=True)
    is_edge_failed = np.zeros([unique_polygon_edges.shape[0]], dtype=bool)
    is_edge_failed[np.greater(edge_counts, 2)] = True
    edge_needs_repaired = np.copy(is_edge_failed)
    is_polygon_edge_failed = is_edge_failed[edge_occurrences]
    failed_polygons = polygon_mesh.edge_index_and_polygon[1, is_polygon_edge_failed]
    failed_polygon_edges = polygon_mesh.edge_per_polygon_edge[is_polygon_edge_failed]
    failed_polygon_edge_id = polygon_mesh.edge_index_and_polygon[0, is_polygon_edge_failed]
    region_failures = polygon_regions[failed_polygons]
    failed_polygon_edges_regions = np.stack(
        [
            region_polygon_index[failed_polygons],
            failed_polygon_edges,
            failed_polygon_edge_id
        ],
        axis=0
    )
    failed_regions = np.unique(region_failures)
    region_failures_dict = dict(
        zip(
            failed_regions,
            [failed_polygon_edges_regions[:, np.equal(region_failures, region_id)] for region_id in failed_regions]
        )
    )
    for region_index, failures in region_failures_dict.items():
        region = non_transparent_regions[region_index]
        region_mesh = Mesh(region.polygons)
        polygon_edge_edge_id_map = coo_array(
            (region_mesh.edge_index_and_polygon[0], (region_mesh.edge_index_and_polygon[1], region_mesh.edge_per_polygon_edge))
        )
        region_edges_in_full_mesh_intersection = polygon_edge_edge_id_map[failures[0], failures[1]].toarray()
        is_edge_in_full_intersection = np.zeros([region_mesh.edge_list.shape[1]], dtype=bool)
        is_edge_in_full_intersection[region_edges_in_full_mesh_intersection] = True
        unique_region_polygon_edges, region_edge_occurrences, region_edge_counts = np.unique(region_mesh.edge_index_and_polygon[0],
                                                                       return_counts=True, return_inverse=True)
        is_edge_interior = np.zeros([region_mesh.edge_list.shape[1]], dtype=bool)
        is_edge_interior[unique_region_polygon_edges[np.greater(region_edge_counts, 1)]] = True
        should_remove_region_edge = is_edge_in_full_intersection & is_edge_interior
        failed_edges_in_repair = failures[2, should_remove_region_edge[region_edges_in_full_mesh_intersection]]
        edge_needs_repaired[failed_edges_in_repair] = False
        is_edge_remaining = np.logical_not(should_remove_region_edge)
        vertex_connection_list = np.concat([
            region_mesh.edge_list[:, is_edge_remaining],
            np.roll(region_mesh.edge_list[:, is_edge_remaining], 1, axis=0)
        ], axis=1)
        should_remap_vertex = np.any(region_mesh.vertex_polygon_lookup[:, failures[0]].toarray(), axis=1)
        vertices_to_remap = np.flatnonzero(should_remap_vertex)
        remapping_vertex_connection_list = vertex_connection_list[
            :,
            np.all(should_remap_vertex[vertex_connection_list], axis=0)
        ]

        vertex_connection_matrix = coo_array(
            ([True] * remapping_vertex_connection_list.shape[1], remapping_vertex_connection_list),
            shape=[region_mesh.vertex_list.shape[1]] * 2
        ).toarray()
        while vertices_to_remap.shape[0] > 0:
            start_vertex = int(vertices_to_remap[0])
            vertex_ordering, predecessors = depth_first_order(vertex_connection_matrix, start_vertex, directed=False, return_predecessors=True)
            ordered_vertex_is_start_neighbor = vertex_connection_matrix[start_vertex, vertex_ordering]
            if np.sum(ordered_vertex_is_start_neighbor) > 1:
                traversal_vertex = vertex_ordering[
                    int(vertex_ordering.shape[0] - np.argmax(np.flip(ordered_vertex_is_start_neighbor)) - 1)
                ]
                new_polygon = [start_vertex]
                while traversal_vertex != start_vertex:
                    new_polygon.append(traversal_vertex)
                    traversal_vertex = predecessors[traversal_vertex]
                region.polygons.append(region_mesh.vertex_list[:, new_polygon])
            keep_vertex = np.ones([region_mesh.vertex_list.shape[1]], dtype=bool)
            keep_vertex[vertex_ordering] = False
            vertices_to_remap = vertices_to_remap[keep_vertex[vertices_to_remap]]
            vertex_connection_matrix[vertex_ordering] = False
            vertex_connection_matrix[:, vertex_ordering] = False
        region.polygons = [polygon for polygon_index, polygon in enumerate(region.polygons) if polygon_index not in failures[0]]



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
    cross_region_pass(regions)