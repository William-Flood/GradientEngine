use numpy::{PyArray, PyArray2, PyArray3, PyArrayMethods, PyUntypedArrayMethods};
use crate::mesh::{Vertex, Edge};
use pyo3::*;
use pyo3::exceptions::PyValueError;
use crate::numpy_utils;

fn check_containment(y1: f32, y2: f32, y3: f32, y4: f32, x1: f32, x2: f32 , x3: f32, x4: f32) -> bool {
    let aligned;
    if x1 != x2 {
        let slope = (y2 - y1) / (x2 - x1);
        let zero_1 = y1 - slope * x1;
        let zero_2 = y3 - slope * x3;
        aligned = zero_1 == zero_2;
    }
    else if y1 != y2 {
        aligned = x1 == x3;
    }
    else if x3 != x4 {
        let slope_2 = (y3 - y4) / (x3 - x4);
        let zero_2 = y3 - slope_2 * x3;
        let line_2_at_x_1 = zero_2 + slope_2 * x1;
        aligned = y1 == line_2_at_x_1;
    }
    else if y3 != y4 {
        aligned = x1 == x3;
    }
    else {
        return x1 == x3 && y1 == y3;
    }
    if aligned {
        if y1 > y2 {
            return (y3 < y1 && y3 > y2) || (y4 < y1 && y4 > y2);
        }
        else if y1 < y2 {
            return (y3 > y1 && y3 < y2) || (y4 > y1 && y4 < y2);
        }
        else if x1 > x2{
            return (x3 < x1 && x3 > x2) || (x4 < x1 && x4 > x2);
        }
        else if x1 < x2 {
            return (x3 > x1 && x3 < x2) || (x4 > x1 && x4 < x2);
        }
        else {
            if y3 > y4 {
                return y1 < y3 && y1 > y4;
            }
            else if y3 < y4 {
                return y1 > y3 && y1 < y4;
            }
            else if x3 > x4{
                return x1 < x3 && x1 > x4;
            }
            else if x3 < x4 {
                return x1 > x3 && x1 < x4;
            }
            else {
                panic!("Missed edge case in parallel intersection test")
            }
        }
    }
    else {
        return false;
    }
}

fn check_intersections(y1: f32, y2: f32, y3: f32, y4: f32, x1: f32, x2: f32 , x3: f32, x4: f32) -> bool {
    let det = ((x1 - x2) * (y3 - y4) -  (y1 - y2) * (x3 - x4)) as f32;
    if det == 0.0 {
        return check_containment(y1, y2, y3, y4, x1, x2, x3, x4);
    }
    let t = 
        ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / 
        det
    ;

    let u = 
        ((y1 - y2) * (x1 - x3) - (x1 - x2) * (y1 - y3)) /
        det
    ;
    let intersection_in_1 = (t > 0.0) && (t < 1.0);
    let intersection_in_2 = (u > 0.0) && (u < 1.0);
    let intersect = intersection_in_1 && intersection_in_2;
    intersect
}

pub fn check_edge_intersection(edge_1: &Edge, edge_2: &Edge, vertices: &[Vertex]) -> bool {
    let y1 = vertices[edge_1.vertex_1].y as f32;
    let y2 = vertices[edge_1.vertex_2].y as f32;
    let y4 = vertices[edge_2.vertex_1].y as f32;
    let y3 = vertices[edge_2.vertex_2].y as f32;
    let x1 = vertices[edge_1.vertex_1].x as f32;
    let x2 = vertices[edge_1.vertex_2].x as f32;
    let x4 = vertices[edge_2.vertex_1].x as f32;
    let x3 = vertices[edge_2.vertex_2].x as f32;
    check_intersections(y1, y2, y3, y4, x1, x2, x3, x4)
}

pub fn check<'py>(
    py: Python<'py>,
    segments_1: Bound<'py, PyArray3<i32>>,
    segments_2: Bound<'py, PyArray3<i32>>
) -> PyResult<Bound<'py, PyArray2<bool>>> {
    let segment_1_view = segments_1.readonly();
    let segments_1_point_count = *segments_1.shape().get(1).ok_or("No point count!").
        map_err(|e| PyValueError::new_err(e.to_string()))?;
    let segments_1_vec = numpy_utils::numpy_to_vec(&segment_1_view);
    let segment_2_view = segments_2.readonly();
    let segments_2_point_count = *segments_2.shape().get(1).ok_or("No point count!").
        map_err(|e| PyValueError::new_err(e.to_string()))?;
    let segments_2_vec = numpy_utils::numpy_to_vec(&segment_2_view);
    let mut intersection_detections = Vec::with_capacity(segments_1_point_count * segments_2_point_count);
    for segment_1_index in 0..segments_1_point_count {
        for segment_2_index in 0..segments_2_point_count {
            let stride_1_0 = segments_1_point_count * 2;
            let stride_1_1 = 2;
            let stride_1_2 = 1;
            let stride_2_0 = segments_2_point_count * 2;
            let stride_2_1 = 2;
            let stride_2_2 = 1;
            intersection_detections.push(
                check_intersections(
                    segments_1_vec[segment_1_index * stride_1_1 ] as f32,
                    segments_1_vec[segment_1_index * stride_1_1 + stride_1_2] as f32,
                    segments_2_vec[segment_2_index * stride_2_1] as f32,
                    segments_2_vec[segment_2_index * stride_2_1 + stride_2_2] as f32,
                    segments_1_vec[segment_1_index * stride_1_1 + stride_1_0] as f32,
                    segments_1_vec[segment_1_index * stride_1_1 + stride_1_0 + stride_1_2] as f32,
                    segments_2_vec[segment_2_index * stride_2_1 + stride_2_0] as f32,
                    segments_2_vec[segment_2_index * stride_2_1 + stride_2_0  + stride_2_2] as f32
                )
            )
        }
    }
    let point_array_flat = PyArray::from_vec(py, intersection_detections);
    let point_array = point_array_flat.reshape((segments_1_point_count, segments_2_point_count)).
        map_err(|e| PyValueError::new_err(e.to_string()))?;
    Ok(point_array)
}