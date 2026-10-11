from fill_gradient import subdivided_border_tangent_interpolation_fill, closest_and_opposite_interpolation_fill
import argparse
import os
import time
import math
import cProfile
import pstats
import io
import gradengc
import gradengrs
from util.inspection_utils import *
import os
from gradengrs import get_borders_dict
from scipy.spatial import KDTree
from polygon.cut_out_quads import cut_up_to_quads


def build_default_output_filename(input_filename):
    """
    Adds 'Gradient' before the file extension.
    Example:
        image.png -> imageGradient.png
    """
    base, ext = os.path.splitext(input_filename)
    return f"{base}Gradient{ext}"


def build_mask_filename(input_filename):
    """
    Adds 'Gradient' before the file extension.
    Example:
        image.png -> imageGradient.png
    """
    base, ext = os.path.splitext(input_filename)
    default_name = f"{base}Mask{ext}"
    if os.path.isfile(default_name):
        return default_name
    else:
        return None


def closest_and_opposite_main():
    parser = argparse.ArgumentParser(description="An image processing utility that blends brightness values in an image")

    parser.add_argument("guide_image_file")

    parser.add_argument(
        "--result_image_file", type=str, default="",
        help="The name of the output file"
    )

    parser.add_argument(
        "--batch_stripe_distance", type=int, default=5,
        help="The size of the rectangles used to interpolate between"
    )

    parser.add_argument(
        "--region_proportion_threshold", type=float, default=0.01,
        help="A minimum threshold used to determine which brightness values to pass into the region identification step - any brightness values representing less than this fraction will be converted to the nearest matching valid value"
    )

    args = parser.parse_args()

    # Generate default output filename if omitted
    result_image_file = (
        args.result_image_file
        if args.result_image_file
        else build_default_output_filename(args.guide_image_file)
    )

    start_time = time.time()
    closest_and_opposite_interpolation_fill(
        guide_image_file=args.guide_image_file,
        result_image_file=result_image_file,
        batch_stripe_distance=args.batch_stripe_distance,
        region_proportion_threshold=args.region_proportion_threshold
    )
    print(f"Elapsed: {time.time() - start_time}")


def subdivided_border_main():

    parser = argparse.ArgumentParser(description="An image processing utility that blends brightness values in an image")

    parser.add_argument("guide_image_file")

    parser.add_argument(
        "--result_image_file", type=str, default="",
        help="The name of the output file"
    )

    parser.add_argument(
        "--mask_file_name", type=str, default="",
        help="The name of a mask file used to prevent certain regions of the image from being blended.  Defaults to the name of the input image plus 'Mask', if that file exists"
    )
    parser.add_argument(
        "--region_defuzz_threshold", type=int, default=10,
        help="The minimum size of a region - any smaller than this will be merged into the closest neighboring region"
    )

    parser.add_argument(
        "--sideways_cut_penalty", type=int, default=100,
        help="A multiplier used to encourage the application to make cuts in a uniform direction when separating regions with holes"
    )

    parser.add_argument(
        "--border_defuzz_threshold", type=int, default=5,
        help="The minimum size of a border - any smaller than this will be removed and the connected borders pinched together"
    )

    parser.add_argument(
        "--border_traversal_failure_tolerance", type=int, default=5,
        help="The maximum size in a gap left by the border walk algorithm - if the algorithm fails to map more points than this, processing will halt and the program will highlight the failed pixels in the file indicated by validation_highlight_file_name"
    )

    parser.add_argument(
        "--region_proportion_threshold", type=float, default=0.01,
        help="A minimum threshold used to determine which brightness values to pass into the region identification step - any brightness values representing less than this fraction will be converted to the nearest matching valid value"
    )

    parser.add_argument(
        "--decimate_deviation_cutoff", type=int, default=3,
        help="The parameter for the Ramer-Douglas-Peucker algorithm for decimating region borders"
    )

    parser.add_argument(
        "--edge_subdivide_ratio", type=float, default=3.0,
        help="Used to determine when to subdivide an edge when splitting polygons into convex regions"
    )

    parser.add_argument(
        "--config_file_name", type=str, default="",
        help="The name of a config file used to store parameters that aren't expected to change between invocations of the program - primarily for performance tuning"
    )

    parser.add_argument(
        "--mesh_smooth_convergence_ratio", type=float, default=0.05,
        help="A threshold used to signal completion of the polygon smoothing algorithm - smaller values produce more smoothing"
    )

    parser.add_argument(
        "--polygon_subdivisions", type=int, default=2,
        help="The number of times to subdivide the polygons in the mesh"
    )

    parser.add_argument(
        "--validation_highlight_file_name", type=str, default="validation_failures.png",
        help="Used to highlight issues in the input image that prevent proper processing"
    )

    parser.add_argument(
        "--validation_fix_file_name", type=str, default="validation_fixes.png",
        help="Used to suggest fixes to issues in the input image that prevent proper processing"
    )

    parser.add_argument(
        "--stripes", type=int, default=255,
        help="The number of stripes to break the smoothed image back into - if set to 255, the image is outputted without discretizing"
    )

    parser.add_argument(
        "--profile", action="store_true",
        help="Sets the profiler on"
    )

    args = parser.parse_args()

    # Generate default output file name if omitted
    result_image_file = (
        args.result_image_file
        if args.result_image_file
        else build_default_output_filename(args.guide_image_file)
    )

    # Generate mask file name if omitted
    mask_file_name = (
        args.mask_file_name
        if args.mask_file_name
        else build_mask_filename(args.guide_image_file)
    )

    if args.profile:
        with cProfile.Profile() as pr:
            # pr.enable()
            subdivided_border_tangent_interpolation_fill(
                args.guide_image_file,
                result_image_file,
                mask_file_name=mask_file_name,
                region_defuzz_threshold=args.region_defuzz_threshold,
                sideways_cut_penalty=args.sideways_cut_penalty,
                border_defuzz_threshold=args.border_defuzz_threshold,
                border_traversal_failure_tolerance=args.border_traversal_failure_tolerance,
                region_proportion_threshold=args.region_proportion_threshold,
                decimate_deviation_cutoff=args.decimate_deviation_cutoff,
                edge_subdivide_ratio=args.edge_subdivide_ratio,
                config_file_name=args.config_file_name,
                mesh_smooth_convergence_ratio=args.mesh_smooth_convergence_ratio,
                polygon_subdivisions=args.polygon_subdivisions,
                validation_highlight_file_name=args.validation_highlight_file_name,
                stripes=args.stripes
            )
            pr.disable()
            s = io.StringIO()
            sort_by = pstats.SortKey.CUMULATIVE
            ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
            ps.print_stats()
            print(s.getvalue())
    else:
        start_time = time.time()
        subdivided_border_tangent_interpolation_fill(
            args.guide_image_file,
            result_image_file,
            mask_file_name=mask_file_name,
            region_defuzz_threshold=args.region_defuzz_threshold,
            sideways_cut_penalty=args.sideways_cut_penalty,
            border_defuzz_threshold=args.border_defuzz_threshold,
            border_traversal_failure_tolerance=args.border_traversal_failure_tolerance,
            region_proportion_threshold=args.region_proportion_threshold,
            decimate_deviation_cutoff=args.decimate_deviation_cutoff,
            edge_subdivide_ratio=args.edge_subdivide_ratio,
            config_file_name=args.config_file_name,
            mesh_smooth_convergence_ratio=args.mesh_smooth_convergence_ratio,
            polygon_subdivisions=args.polygon_subdivisions,
            validation_highlight_file_name=args.validation_highlight_file_name,
            stripes=args.stripes
        )
        print(f"Elapsed: {time.time() - start_time}")


def test_reduce():
    region = np.reshape(np.indices([2000, 3000]), [2, -1]) + 5

    reduce_start = time.time()
    region_borders = np.array(get_borders_dict([2010, 3010], [region])[0])
    border_map_time = time.time() - reduce_start
    border_tree = KDTree(region_borders)
    border_matches = border_tree.query(region.T)
    border_distances = border_matches[0]
    max_distance = np.max(border_distances)
    middle = np.flatnonzero(np.equal(border_distances, max_distance))
    reduce_time = time.time() - reduce_start
    return middle


if __name__ == "__main__":
    # cut_up_to_quads([])
    subdivided_border_main()