# Gradient Engine
A drawing utility application intended to draw smooth gradients of arbitrary shapes.  The application takes a template file with regions of contiguous, uniform grayscale values and interpolates between the region boundaries to produce the resulting gradient.

# Usage
Call main.py using the template file name as the first positional argument.  The following additional optional flags are available as follows:

-result_image_file: The name of the save file for the blended image.  If omitted, "Gradient" will be appended to the end of the file name, before the extension.

-mask_file_name: The name of a mask file used to prevent certain regions of the image from being blended.  Defaults to the name of the input image plus 'Mask', if that file exists.

-region_defuzz_threshold: The minimum size of a region - any smaller than this will be merged into the closest neighboring region.

-sideways_cut_penalty: A multiplier used to encourage the application to make cuts in a uniform direction when separating regions with holes.

-border_defuzz_threshold: The minimum size of a border - any smaller than this will be removed and the connected borders pinched together.

-border_traversal_failure_tolerance: The maximum size in a gap left by the border walk algorithm - if the algorithm fails to map more points than this, processing will halt and the program will highlight the failed pixels in the file indicated by validation_highlight_file_name.

-region_proportion_threshold: A minimum threshold used to determine which brightness values to pass into the region identification step - any brightness values representing less than this fraction will be converted to the nearest matching valid value.

-decimate_deviation_cutoff: The parameter for the Ramer-Douglas-Peucker algorithm for decimating region borders.

-config_file_name: The name of a config file used to store parameters that aren't expected to change between invocations of the program - primarily for performance tuning.

-mesh_smooth_convergence_ratio: A threshold used to signal completion of the polygon smoothing algorithm - smaller values produce more smoothing.

-polygon_subdivisions: The number of times to subdivide the polygons in the mesh.

-validation_highlight_file_name: Used to highlight issues in the input image that prevent proper processing.

-validation_fix_file_name: Used to suggest fixes to issues in the input image that prevent proper processing.

-stripes: The number of stripes to break the smoothed image back into - if set to 255, the image is outputted without discretizing.

-profile: Sets the profiler on.

# AI disclosure:
No LLM-generated code was used in the development of the project.  ChatGPT was used to inspect the completed code for bugs, as well as sparing use in debugging during early development of the C module and OpenGL code.
