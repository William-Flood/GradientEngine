/// A Python module implemented in Rust. The name of this module must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
mod border_finder;
mod triangle_cutter;
mod double_key_tree;
mod numpy_utils;
mod mesh;
mod find_index_in;
mod smooth_polys;
mod mesh_python_interface;
mod decimate;
mod merge;
mod edge_intersection_handler;
mod segment_intersection;
#[pyo3::pymodule]
mod gradengrs {
  use pyo3::Bound;
use pyo3::prelude::*;
  use pyo3::pyfunction;
use pyo3::types::PyList;
  use pyo3::types::PyDict;
  use numpy::{PyArray, Ix2, PyArray2, PyArray3};
  use crate::mesh_python_interface;
  use crate::triangle_cutter;
  #[pymodule_export]
  use crate::mesh_python_interface::PolygonResult;
  use crate::smooth_polys;
  use crate::decimate;
  use crate::edge_intersection_handler;
  use crate::segment_intersection;

  #[pyfunction]
  fn get_borders_dict<'py>(
    py: Python<'py>,
    image_size: Vec<usize>,
    region_points: Bound<'py, PyList>
  ) -> PyResult<Bound<'py, PyDict>> {
    super::border_finder::get_borders_dict(py, image_size, region_points)
  }

  #[pyfunction]
  fn get_double_borders_dict<'py>(
    py: Python<'py>,
    image_size: Vec<usize>,
    region_map: Bound<'py, PyArray<i64, Ix2>>,
    point_values: Bound<'py, PyArray<i64, Ix2>>
  ) -> PyResult<Bound<'py, PyDict>> {
    super::border_finder::get_double_border_dict(py, image_size, region_map, point_values)
  }

  #[pyfunction]
  fn cut_out_trianges<'py> (
    py: Python<'py>,
    polygons: Bound<'py, PyList>
  ) -> PyResult<Bound<'py, PyList>> {
    let polygon_vector = mesh_python_interface::get_polygon_vector(polygons)?;
    let (rectancles, vertices) = triangle_cutter::cut_out_trianges(polygon_vector);
    mesh_python_interface::get_polygon_results(py, rectancles, vertices)
  }

  #[pyfunction]
  fn smooth_polygons<'py> (
    py: Python<'py>,
    polygons: Bound<'py, PyList>,
    convergence_ratio: f32
  ) -> PyResult<Bound<'py, PyList>> {
    let polygon_vector = mesh_python_interface::get_polygon_vector(polygons)?;
    let (rectancles, vertices) = smooth_polys::smooth_polygons(polygon_vector, convergence_ratio);
    mesh_python_interface::get_polygon_results(py, rectancles, vertices)
  }

  #[pyfunction]
  fn test_tree<'py>(
    list: Vec<usize>
  ) -> PyResult<Vec<usize>> {
    super::mesh_python_interface::test_tree(list)
  }

  #[pyfunction]
  fn decimate_mesh<'py> (
    py: Python<'py>,
    polygons: Bound<'py, PyList>,
    keep_distance: i32) -> PyResult<Bound<'py, PyList>> {
    let polygon_vector = mesh_python_interface::get_polygon_vector(polygons)?;
    let (polygons, vertices) = decimate::decimate(polygon_vector, keep_distance);
    mesh_python_interface::get_polygon_results(py, polygons, vertices)
  }
  #[pyfunction]
  fn remove_intersecting_edges<'py> (
    py: Python<'py>,
    polygons: Bound<'py, PyList>) -> PyResult<Bound<'py, PyList>> {
      let polygon_vector = mesh_python_interface::get_polygon_vector(polygons)?;
      let (polygons, vertices) = 
        edge_intersection_handler::remove_intersecting_edges(polygon_vector);
      mesh_python_interface::get_polygon_results(py, polygons, vertices)
    }

  #[pyfunction]
  fn check_intersections<'py>(
    py: Python<'py>,
      segments_1: Bound<'py, PyArray3<i32>>,
      segments_2: Bound<'py, PyArray3<i32>>
  ) -> PyResult<Bound<'py, PyArray2<bool>>> {
    segment_intersection::check(py, segments_1, segments_2)
  }
}