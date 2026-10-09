
    use crate::mesh::{Vertex, Edge};
    use crate::{find_index_in, mesh};


    pub struct VertexMerger<'a> {
        pub vertices: &'a mut Vec<Vertex>,
        pub old_ids: Vec<usize>,
        pub new_old_map: Option<Vec<usize>>
    }

    impl<'a> VertexMerger<'a> {
        pub fn new(vertices: &'a mut Vec<Vertex>) -> Self {
            let old_ids = vertices.iter().map(|v| v.id).collect();
            VertexMerger { vertices, old_ids, new_old_map: None }
        }
        pub fn insert (&mut self, y: usize, x: usize) {
            let new_id = self.vertices.len();
            find_index_in::insert_into_double_key_ordered(
                y,
                x,
                self.vertices,
                || Vertex { id: new_id, y: y, x: x, edges: Vec::new() }
            );
        }
        pub fn map_old_and_refresh_ids(&mut self) {
            let mut is_old = vec![false; self.vertices.len()];
            for old_id in &self.old_ids {
                is_old[*old_id] = true;
            }
            let mut new_old_map = Vec::with_capacity(self.old_ids.len());
            for (new_position, vertex) in self.vertices.iter_mut().enumerate() {
                if is_old[vertex.id] {
                    new_old_map.push(new_position);
                }
                vertex.id = new_position;
            }
            self.new_old_map = Some(new_old_map);
        }
        pub fn find_in(&self, y: usize, x:usize) -> Option<usize> {
            find_index_in::find_index_in(
                    y, 
                    x, 
                    self.vertices)
        }
    }

    
    pub struct EdgeMerger<'a> {
        pub edges: &'a mut Vec<Edge>,
        pub old_ids: Vec<usize>,
        pub new_old_map: Option<Vec<usize>>
    }

    impl<'a> EdgeMerger<'a> {
        pub fn new(edges: &'a mut Vec<Edge>) -> Self {
            let old_ids = edges.iter().map(|v| v.id).collect();
            EdgeMerger { edges, old_ids, new_old_map: None }
        }
        pub fn insert (&mut self, vertex_1: usize, vertex_2: usize, vertex_vector: &Vec<Vertex>) {
            let new_id = self.edges.len();
            let edge_length = mesh::get_distances_of(vertex_vector, vertex_1, vertex_2);
            find_index_in::insert_into_double_key_ordered(
                vertex_1,
                vertex_2,
                self.edges,
                || Edge { id: new_id, vertex_1, vertex_2, polygons: Vec::new(), edge_length }
            );
        }
        pub fn map_old_and_refresh_ids(&mut self) {
            let mut is_old = vec![false; self.edges.len()];
            for old_id in &self.old_ids {
                is_old[*old_id] = true;
            }
            let mut new_old_map = Vec::with_capacity(self.old_ids.len());
            for (new_position, edge) in self.edges.iter_mut().enumerate() {
                if is_old[edge.id] {
                    new_old_map.push(new_position);
                }
                edge.id = new_position;
            }
            self.new_old_map = Some(new_old_map);
        }
        pub fn find_in(&self, vertex_1: usize, vertex_2: usize) -> Option<usize> {
            find_index_in::find_index_in(
                vertex_1,
                vertex_2,
                    self.edges)
        }
        pub fn remap_vertex_lists(&mut self, vertex_merger: &VertexMerger) {
            let new_old_index_map = vertex_merger.new_old_map.as_ref().expect("Vertex old to new map retrieved before binding");
            for edge in &mut *self.edges {
                edge.vertex_1 = new_old_index_map[edge.vertex_1];
                edge.vertex_2 = new_old_index_map[edge.vertex_2];
            }
        }
    }