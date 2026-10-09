use crate::merge::VertexMerger;
use crate::mesh;
use crate::mesh::{Edge, Vertex, Polygon};

fn merge_edge(vertices: &mut Vec<Vertex>, edges: &mut Vec<Edge>, polygons: &mut Vec<Polygon>, edge_id: usize) {
    let edge = &mut edges[edge_id];
    edge.polygons = Vec::new();
    let vertex_1_id = edge.vertex_1;
    let vertex_2_id = edge.vertex_1;
    let merge_vertex_1 = & vertices[vertex_1_id];
    let merge_vertex_2 = & vertices[vertex_2_id];
    let merge_y = (merge_vertex_1.y + merge_vertex_2.y) / 2;
    let merge_x = (merge_vertex_1.x + merge_vertex_2.x) / 2;
    let mut vertex_merger = VertexMerger::new(vertices);
    vertex_merger.insert(merge_y, merge_x);
    vertex_merger.map_old_and_refresh_ids();
    let vertex_old_new_map = vertex_merger.new_old_map.as_ref().expect("New old map did not populate");
    let new_id = vertex_merger.find_in(merge_y, merge_x).expect("New vertex is missing in new list");
    for edge in edges {
        if edge.vertex_1 == vertex_1_id {
            edge.vertex_1 = new_id;
        }
        else {
            edge.vertex_1 = vertex_old_new_map[edge.vertex_1];
        }
        if edge.vertex_2 == vertex_1_id {
            edge.vertex_2 = new_id;
        }
        else {
            edge.vertex_2 = vertex_old_new_map[edge.vertex_2];
        }
    }
    for polygon in polygons {
        polygon.edges = polygon.edges.iter().filter(|e| **e != edge_id).map(|e| *e).collect();
        let mut found_old = false;
        let mut new_vertices = Vec::new();
        for vertex in polygon.vertices.clone() {
            if vertex == vertex_1_id || vertex == vertex_2_id {
                if !found_old {
                    found_old = true;
                    new_vertices.push(new_id);
                }
            } else {
                new_vertices.push(vertex_old_new_map[vertex_1_id]);
            }
        }
    }
}

fn edge_id_to_merge(edges: &Vec<Edge>, keep_length: i32) -> Option<usize> {
    let edge_to_merge_res = edges.iter().find(|e| e.edge_length < keep_length && e.polygons.len() > 0);
    edge_to_merge_res.map(|e| e.id)
}

pub fn decimate(
    polygon_coords: Vec<Vec<(usize, usize)>>,
    keep_length: i32
) -> (Vec<Polygon>, Vec<Vertex>) {
    let mut vertex_list = mesh::get_vertices(&polygon_coords);
    let mut edge_list = mesh::get_edge_vector(&polygon_coords, &vertex_list);
    let mut polygons = mesh::get_polygons(&polygon_coords, &vertex_list, &edge_list);
    mesh::connect_mesh(&mut vertex_list,  &mut edge_list, &polygons);
    while let Some(edge_to_merge) =  edge_id_to_merge(&edge_list, keep_length) {
        merge_edge(&mut vertex_list, &mut edge_list, &mut polygons, edge_to_merge);
    }
    (polygons, vertex_list)
}