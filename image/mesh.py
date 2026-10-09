from OpenGL.GL import *
import numpy as np

DATA_TYPE_COLORED_VERTEX = np.dtype({
    'names': ['x', 'y', 'z', 'color'],
    'formats': [np.float32, np.float32, np.float32, np.float32],
    "offsets": [0, 4, 8, 12],
    'itemsize': 16
})

class Mesh:
    def __init__(self):
        self.VAO = glGenVertexArrays(1)
        self.VBO, self.EBO = glGenBuffers(2)
        self.index_count = 0

    def builds_quads(self, vertices, indices) -> "Mesh":
        glBindVertexArray(self.VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        attribute_index = 0
        size = 3
        offset = 0
        stride = DATA_TYPE_COLORED_VERTEX.itemsize
        glVertexAttribPointer(attribute_index, size, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        attribute_index += 1
        offset += 12
        size = 1
        glVertexAttribPointer(
            attribute_index, size, GL_FLOAT, GL_FALSE,
            stride, ctypes.c_void_p(offset))
        glEnableVertexAttribArray(attribute_index)

        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        self.index_count = indices.shape[0]
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        return self


    def draw(self):
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    def destroy(self):
        glDeleteVertexArrays(1, (self.VAO,))
        glDeleteBuffers(1, (self.VBO,))