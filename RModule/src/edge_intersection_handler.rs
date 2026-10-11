use crate::mesh;
use crate::mesh::{Polygon, Vertex, Edge};
use crate::segment_intersection;
use std::{rc::Rc};


struct NavigationNode {
    edge: usize,
    vertex: usize,
    last: Option<Rc<NavigationNode>>
}

struct MapResults {
    new_poly_vertices: Vec<usize>,
    new_poly_edges: Vec<usize>
}

struct IntSet {
    has_value: Vec<bool>,
    active: Vec<bool>,
    value_in: Vec<usize>,
    values: Vec<usize>
}


impl IntSet {
    fn new(size: usize) -> Self {
        IntSet { has_value: vec![false; size], value_in: vec![0; size], values: Vec::new(), active: vec![false; size] }
    }
    fn contains(&self, value: usize) -> bool {
        self.active[value]
    }
    fn insert(&mut self, value: usize) {
        if !self.has_value[value] {
            self.has_value[value] = true;
            self.active[value] = true;
            self.value_in[value] = self.values.len();
            self.values.push(value);
        }
        else if !self.active[value] {
            self.active[value] = true;
        }
    }
    fn remove(&mut self, value: usize) {
        if self.active[value] {
            self.active[value] = false;
        }
    }
    fn iter(&self) -> impl Iterator<Item = &usize> {
        self.values.iter().filter(|v| self.active[**v])
    }
    fn clone(&self) -> Self{
        IntSet { has_value: self.has_value.clone(), value_in: self.value_in.clone(), values: self.values.clone(), active: self.active.clone() }
    }
    fn is_empty(&self) -> bool {
        return !self.values.iter().any(|v| self.active[*v]);
    }
    fn from(values: &[usize], size: usize) -> Self {
        let mut new_int_set = IntSet::new(size);
        for &value in values {
            new_int_set.insert(value);
        }
        new_int_set
    }
    fn len(&self) -> usize {
        self.values.iter().filter(|v| self.active[**v]).count()
    }
    fn difference(&self, other: &IntSet) -> IntSet {
        let mut new_int_set = IntSet::new(self.value_in.len());
        for &value in self.values.iter().filter(|v| self.active[**v]) {
            if !other.contains(value) {
                new_int_set.insert(value);
            }
        }
        new_int_set
    }
}


fn map_available_vertices(
        edges: &[Edge], 
        vertices: &[Vertex], 
        edges_to_remap: &IntSet, 
        start_edge_id: usize) -> IntSet {
    let mut navigation_stack = vec![NavigationNode {edge: start_edge_id, vertex: edges[start_edge_id].vertex_2, last: None}];

    let mut navigation_set = IntSet::from(&vec![edges[start_edge_id].vertex_2], vertices.len());
    while let Some(navigation_node) = navigation_stack.pop() {
        let search_vertex = &vertices[navigation_node.vertex];
        let candidate_edges_id = &search_vertex.edges;
        let candidate_remapping_edges: Vec<usize> = candidate_edges_id.iter().
            filter(|ei| edges_to_remap.contains(**ei)).map(|rei| *rei)
            .collect();
        for candidate_id in candidate_remapping_edges {
            let next_edge = &edges[candidate_id];
            if !navigation_set.contains(next_edge.vertex_1) {
                navigation_stack.push(NavigationNode {edge: candidate_id, vertex: next_edge.vertex_1, last: None});
                navigation_set.insert(next_edge.vertex_1);
            }
            else if !navigation_set.contains(next_edge.vertex_2) {
                navigation_stack.push(NavigationNode {edge: candidate_id, vertex: next_edge.vertex_2, last: None});
                navigation_set.insert(next_edge.vertex_2);
            }
        }

    }
    navigation_set
}


fn filter_dangling_vertices(
        vertices_to_filter: IntSet, 
        vertices: &[Vertex],
        edges_to_remap: &IntSet,
) -> IntSet {
    let mut filtered_set = IntSet::new(vertices.len());
    for &vertex_id in vertices_to_filter.iter() {
        let vertex = &vertices[vertex_id];
        let valid_connections_for_loop = vertex.edges.iter().filter(|eid| edges_to_remap.contains(**eid)).count() > 1;
        if valid_connections_for_loop {
            filtered_set.insert(vertex_id);
        }
    }
    filtered_set
}


fn map_new_polygon(
        edges: &[Edge], 
        vertices: &[Vertex],
        edges_to_remap: &IntSet,
        start_edge_id: usize) -> MapResults {
    let full_available_vertices = map_available_vertices(edges, vertices, edges_to_remap, start_edge_id);
    let available_vertices = filter_dangling_vertices(full_available_vertices, vertices, edges_to_remap);
    if available_vertices.is_empty() {
        return MapResults { new_poly_vertices: Vec::new(), new_poly_edges: Vec::new() };
    }
    // for &found in available_vertices.iter() {
    //     let found_vert = [vertices[found].y, vertices[found].x];
    //     println!("{found_vert:?}");
    // }
    let mut edge_in_this_poly = vec![false; edges.len()];
    let mut found_vertices = IntSet::new(vertices.len());
    let start_vertex_id = *available_vertices.iter().next().expect("Started search from an empty vertex set");
    let start_vertex = &vertices[start_vertex_id];
    let valid_start_edges: Vec<&usize> = start_vertex.edges.iter().filter(|&&eid| edges_to_remap.contains(eid)).collect();
    let navigation_start_edge = *valid_start_edges[0];
    let navigation_start_vertex;
    if edges[navigation_start_edge].vertex_1 == start_vertex_id {
        navigation_start_vertex = edges[navigation_start_edge].vertex_2;
    }
    else if edges[navigation_start_edge].vertex_2 == start_vertex_id {
        navigation_start_vertex = edges[navigation_start_edge].vertex_1;
    }
    else {
        panic!("Vertex-edge relationship was not mutual when initializing navigation_start_vertex");
    }
    edge_in_this_poly[navigation_start_edge] = true;
    found_vertices.insert(start_vertex_id);
    let mut navigation_stack = vec![NavigationNode {edge: navigation_start_edge, vertex: navigation_start_vertex, last: None}];
    let mut seeking_start = true;
    while seeking_start {
        let Some(navigation_node) = navigation_stack.pop() else {break};
        let navigation_vertex_id = navigation_node.vertex;
        found_vertices.insert(navigation_vertex_id);
        edge_in_this_poly[navigation_node.edge] = true;
        let search_vertex = &vertices[navigation_vertex_id];
        let candidate_edges_id = &search_vertex.edges;
        let candidate_remapping_edges: Vec<&usize> = candidate_edges_id.iter().
            filter(|ei| edges_to_remap.contains(**ei))
            .collect();
        let navigation_reference_node = Rc::new(navigation_node);
        for &candidate_id in candidate_remapping_edges {
            if !edge_in_this_poly[candidate_id] {
                let next_edge = &edges[candidate_id];
                let next_vertex;
                if next_edge.vertex_1 != search_vertex.id {
                    next_vertex = next_edge.vertex_1;
                }
                else if next_edge.vertex_2 != search_vertex.id {
                    next_vertex = next_edge.vertex_2;
                }
                else {
                    panic!("Vertex-edge relationship was not mutual when navigating");
                }
                if !found_vertices.contains(next_vertex) && available_vertices.contains(next_vertex) {
                    navigation_stack.push(NavigationNode {edge: candidate_id, vertex: next_vertex, last: Some(Rc::clone(&navigation_reference_node)) });
                }
                else if next_vertex == start_vertex_id {
                    let remaining_vertices = available_vertices.difference(&found_vertices);
                    let remaining_count = remaining_vertices.len();
                    if remaining_count == 0 {
                        navigation_stack.push(NavigationNode {edge: candidate_id, vertex: next_vertex, last: Some(Rc::clone(&navigation_reference_node)) });
                        seeking_start = false;
                        break;
                    }
                    // else {
                    //     let found_vector: Vec<&usize> = found_vertices.iter().collect();
                    //     let remaing_vector: Vec<&usize> = remaining_vertices.iter().collect();
                    //     println!("Found");
                    //     for &found in found_vector {
                    //         let found_vert = [vertices[found].y, vertices[found].x];
                    //         println!("{found_vert:?}");
                    //     }
                    //     println!("Found");
                    //     for &remaining in remaing_vector {
                    //         let remaining_vert = [vertices[remaining].y, vertices[remaining].x];
                    //         println!("{remaining_vert:?}");
                    //     }
                    //     println!("Still seeking {remaining_count} on {navigation_vertex_id}");
                    // }
                }
            }
        }
        let mut backtracking_node = &navigation_reference_node;
        while Rc::strong_count(&backtracking_node) == 1 {
            found_vertices.remove(backtracking_node.vertex);
            edge_in_this_poly[backtracking_node.edge] = false;
            if let Some(ref last_node) = backtracking_node.last {
                backtracking_node = last_node;
            }
            else {
                break;
            }
        }

    }
    let mut new_poly_vertices = Vec::new();
    let mut new_poly_edges = Vec::new();
    if let Some(start_node) = navigation_stack.pop() {
        let mut polygon_node = &Rc::new(start_node);
        loop {
            new_poly_edges.push(polygon_node.edge);
            new_poly_vertices.push(polygon_node.vertex);
            if let Some(ref next_node) = polygon_node.as_ref().last {
                polygon_node = next_node;
            }
            else {
                break;
            }
        }
    }
    MapResults { new_poly_vertices, new_poly_edges }
}

fn fill_remap_polygons(edge_remap_basis: &IntSet, edge_list: &[Edge], polygons_to_remove: &mut IntSet) {
    for &edge_id in edge_remap_basis.iter() {
        let edge = &edge_list[edge_id];
        let edge_polygons = &edge.polygons;
        for &polygon_id in edge_polygons {
            polygons_to_remove.insert(polygon_id);
        }
    }
}

fn add_remap_edges(edge_list: &[Edge], edges_to_remap: &mut IntSet, 
        polygons: &[Polygon], polygons_to_remove: &IntSet, edges_to_remove: &IntSet) {
    let remap_inclusion_predicate = |pid: &&usize| polygons_to_remove.contains(**pid);
    let remap_border_predicate = |eid: &&usize| edge_list[**eid].polygons.iter()
        .filter(remap_inclusion_predicate).count() == 1;
    for &remap_edge_id in polygons_to_remove.iter()
            .flat_map(|pid| &polygons[*pid].edges)
            .filter(remap_border_predicate) {
        if !edges_to_remove.contains(remap_edge_id) {
            // Filter edges to match exactly one polygon in polygons_to_remove
            edges_to_remap.insert(remap_edge_id);
        }
    }
}

fn add_intersecting_edges(vertices: &[Vertex], edges: &[Edge], mut edges_to_remove: IntSet) -> IntSet {
    for lower_index in 0..(edges.len()) {
        if edges[lower_index].polygons.len() > 2 {
            edges_to_remove.insert(lower_index);
        }
        for upper_index in (lower_index + 1)..(edges.len()) {
            if segment_intersection::check_edge_intersection(
                    &edges[lower_index], 
                    &edges[upper_index], 
                    vertices
                ) {
                if !edges_to_remove.contains(lower_index) && edges[lower_index].polygons.len() > 1 {
                    edges_to_remove.insert(lower_index);
                }
                if !edges_to_remove.contains(upper_index) && edges[upper_index].polygons.len() > 1 {
                    edges_to_remove.insert(upper_index);
                }
            }
        }
    }
    edges_to_remove
}

fn get_vertex_polygon_neighbors(
    vertex: &Vertex, 
    edges: &[Edge], 
    polygons: &[Polygon]
) -> IntSet {
    let mut point_neighbor_polygons = IntSet::new(polygons.len());
    for &edge_id in &vertex.edges {
        let edge = &edges[edge_id];
        for &vertex_polygon_id in &edge.polygons {
            let vertex_polygon = &polygons[vertex_polygon_id];
            for &vertex_polygon_neighbor_id in vertex_polygon.get_unguarded_connections(edges) {
                point_neighbor_polygons.insert(vertex_polygon_neighbor_id);
            }
        }
    }
    point_neighbor_polygons
}

fn cross_z_of_wedge(wedge_center: &Vertex, vertex_1: &Vertex, vertex_2: &Vertex) -> i32 {
    let segment_1_y = (vertex_1.y as i32) - (wedge_center.y as i32);
    let segment_1_x = (vertex_1.x as i32) - (wedge_center.x as i32);
    let segment_2_y = (vertex_2.y as i32) - (wedge_center.y as i32);
    let segment_2_x = (vertex_2.x as i32) - (wedge_center.x as i32);
    segment_1_y * segment_2_x - segment_2_y * segment_1_x
}

fn is_vertex_in_triangle(triangle: &[&Vertex; 3], vertex: &Vertex) -> bool {
    let cross_z_1 = cross_z_of_wedge(triangle[0], &vertex, triangle[1]);
    let cross_z_2 = cross_z_of_wedge(triangle[1], &vertex, triangle[2]);
    let cross_z_3 = cross_z_of_wedge(triangle[2], &vertex, triangle[0]);
    if cross_z_1 >= 0 {
        cross_z_2 >= 0 && cross_z_3 >= 0
    }
    else {
        cross_z_2 <= 0 && cross_z_3 <= 0
    }
}

fn get_polygon_triangles<'a>(polygon: &'a Polygon, vertices: &'a [Vertex]) -> impl IntoIterator<Item = [&'a Vertex; 3]> {
    let polygon_vertex_count = polygon.vertices.len();
    if polygon_vertex_count == 3 {
        vec![[
            &vertices[polygon.vertices[0]],
            &vertices[polygon.vertices[1]],
            &vertices[polygon.vertices[2]]
        ]]
    }
    else if polygon_vertex_count == 4 {
        let mut split_triangle;
        let mut split_opposite_triangle;
        for split_index in 0..4 {
            split_triangle = [
                &vertices[polygon.vertices[split_index]],
                &vertices[polygon.vertices[(split_index + 1) % 4]],
                &vertices[polygon.vertices[(split_index + 3) % 4]]
            ];
            split_opposite_triangle = [
                &vertices[polygon.vertices[(split_index + 1) % 4]],
                &vertices[polygon.vertices[(split_index + 2) % 4]],
                &vertices[polygon.vertices[(split_index + 3) % 4]]
            ];
            let is_split_in_opposing = is_vertex_in_triangle(&split_triangle, &vertices[polygon.vertices[(split_index + 2) % 4]]);
            let is_opposing_in_split = is_vertex_in_triangle(&split_opposite_triangle, &vertices[polygon.vertices[split_index]]);
            if !(is_split_in_opposing || is_opposing_in_split) {
                return vec![split_triangle, split_opposite_triangle];
            }
        }
        split_triangle = [
            &vertices[polygon.vertices[0]],
            &vertices[polygon.vertices[1]],
            &vertices[polygon.vertices[3]]
        ];
        split_opposite_triangle = [
            &vertices[polygon.vertices[1]],
            &vertices[polygon.vertices[2]],
            &vertices[polygon.vertices[3]]
        ];
        return vec![split_triangle, split_opposite_triangle];
    }
    else {
        panic!("{polygon_vertex_count}-gon in list");
    }
}


fn check_vertex_overlap (
    vertex: &Vertex,
    vertices: &[Vertex],
    polygon: &Polygon
) -> bool {
    for &polygon_vertex in &polygon.vertices {
        if vertex.id == polygon_vertex {
            return false;
        }
    }
    for triangle in get_polygon_triangles(polygon, vertices) {
        if is_vertex_in_triangle(&triangle, &vertex) {
            return  true
        }
    }
    return false;
}


fn add_overlapped_vertices(
    vertices: &[Vertex], 
    edges: &[Edge], 
    polygons: &[Polygon],
    mut edges_to_remove: IntSet
) -> IntSet {
    let mut vertex_polygon_pairs = Vec::new();
    for vertex in vertices {
        for &vertex_polygon_neighbor in get_vertex_polygon_neighbors(vertex, edges, polygons).iter() {
            vertex_polygon_pairs.push((vertex, &polygons[vertex_polygon_neighbor]));
        }
        
    }
    let mut already_tested = vec![false; vertices.len() * polygons.len()];
    let polygon_count = polygons.len();
    while let Some((pair_vertex, pair_polygon)) = vertex_polygon_pairs.pop()  {
        already_tested[pair_vertex.id * polygon_count + pair_polygon.id] = true;
        if check_vertex_overlap(pair_vertex, vertices, pair_polygon) {
            for &edge_id in &pair_vertex.edges {
                if edges[edge_id].polygons.len() > 1 {
                    edges_to_remove.insert(edge_id);
                }
                for shared_polygon in edges[edge_id].polygons.iter().map(|pid| &polygons[*pid]) {
                    for shared_polygon_vertex in shared_polygon.vertices.iter()
                    .filter(|vid| !already_tested[*vid * polygon_count + pair_polygon.id])
                    .map(|vid| &vertices[*vid]) {
                        vertex_polygon_pairs.push((shared_polygon_vertex, pair_polygon));
                        let shared_vertex_neighboring_polygons = get_vertex_polygon_neighbors(
                            shared_polygon_vertex, edges, polygons
                        );
                        for &vertex_polygon_neighbor in  shared_vertex_neighboring_polygons.iter()
                                .filter(|pid| !already_tested[shared_polygon_vertex.id * polygon_count + **pid]) {
                            vertex_polygon_pairs.push((shared_polygon_vertex, &polygons[vertex_polygon_neighbor]));
                        }
                    }
                }
            }
        }
    }
    edges_to_remove
}

fn find_edges_to_remove(vertices: &[Vertex], edges: &[Edge], polygons: &[Polygon]) -> IntSet {
    let mut edges_to_remove = IntSet::new(edges.len());
    edges_to_remove = add_intersecting_edges(vertices, edges, edges_to_remove);
    edges_to_remove = add_overlapped_vertices(vertices, edges, polygons, edges_to_remove);
    edges_to_remove
}

pub fn remove_intersecting_edges(polygon_coords: Vec<Vec<(usize, usize)>>) -> (Vec<Polygon>, Vec<Vertex>) {
    let mut vertex_list = mesh::get_vertices(&polygon_coords);
    let mut edge_list = mesh::get_edge_vector(&polygon_coords, &vertex_list);
    let mut polygons = mesh::get_polygons(&polygon_coords, &vertex_list, &edge_list);
    mesh::connect_mesh_unguarded(&mut vertex_list,  &mut edge_list, &polygons);
    let edges_to_remove = find_edges_to_remove(&vertex_list, &edge_list, &polygons);
    let mut polygons_to_remove = IntSet::new(polygons.len());
    fill_remap_polygons(&edges_to_remove, &edge_list, &mut polygons_to_remove);
    let mut edges_to_remap = IntSet::new(edge_list.len());
    add_remap_edges(&edge_list, &mut edges_to_remap, &polygons, &polygons_to_remove, &edges_to_remove);
    let removing_vector: Vec<usize> = polygons_to_remove.iter().copied().collect();
    let mut remapped_edges = IntSet::new(edge_list.len());
    loop {
        let mut any_polygons_remapped = false;
        for &edge_id in edges_to_remap.clone().iter() {
            if edges_to_remap.contains(edge_id) {
                let map_results = map_new_polygon(&edge_list, &vertex_list, &edges_to_remap.difference(&remapped_edges), edge_id);
                if !map_results.new_poly_edges.is_empty() {
                    any_polygons_remapped = true;
                    for &edge_id in &map_results.new_poly_edges {
                        edges_to_remap.remove(edge_id);
                        remapped_edges.insert(edge_id);
                        for &poly_id in &edge_list[edge_id].polygons {
                            if polygons_to_remove.contains(poly_id) {
                            }
                            polygons_to_remove.remove(poly_id);
                        }
                    }
                    let new_poly = Polygon {
                        id: polygons.len(),
                        original_id: polygons.len(),
                        vertices: map_results.new_poly_vertices,
                        edges: map_results.new_poly_edges
                    };
                    polygons.push(new_poly);

                }
            }
        }
        let last_count = polygons_to_remove.len();
        if !polygons_to_remove.is_empty() {
            let mut unmapped_polygon_edges = IntSet::new(edge_list.len());
            for &polygon_id in polygons_to_remove.iter() {
                for &edge_id in &polygons[polygon_id].edges {
                    if !(edges_to_remove.contains(edge_id) || remapped_edges.contains(edge_id)) {
                        unmapped_polygon_edges.insert(edge_id);
                    }
                }
            }
            fill_remap_polygons(&unmapped_polygon_edges, &edge_list, &mut polygons_to_remove);
            edges_to_remap = IntSet::new(edge_list.len());
            add_remap_edges(&edge_list, &mut edges_to_remap, &polygons, &polygons_to_remove, &edges_to_remove);
        }
        if !any_polygons_remapped && last_count == polygons_to_remove.len() {
            break;
        }
    }
    let mut remove_polygon = vec![false; polygons.len()];
    for remove_poly_id in removing_vector {
        remove_polygon[remove_poly_id] = true;
    }
    polygons.retain(|p| !remove_polygon[p.id]);
    (polygons, vertex_list)
}