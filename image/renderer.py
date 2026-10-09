from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from image.mesh import Mesh


def make_shader_module(filename: str, module_type: int) -> int:
    with open(filename, "r") as file:
        source_code = file.readlines()
        return compileShader(source_code, module_type)

def make_shader(vertex_source_file, fragment_source_file) -> int:
    vertex_module = make_shader_module(vertex_source_file, GL_VERTEX_SHADER)
    fragment_module = make_shader_module(fragment_source_file, GL_FRAGMENT_SHADER)
    return compileProgram(vertex_module, fragment_module)

class Renderer:
    SCREEN_COLOR = (0.0, 0.0, 0.0, 0.0)

    def __init__(self, mesh):
        glClearColor(*Renderer.SCREEN_COLOR)
        self.mesh = mesh

        self.shader = make_shader("image/vertex.txt", "image/fragment.txt")

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader)
        self.mesh.draw()

    def destroy(self):
        self.mesh.destroy()
        glDeleteProgram(self.shader)
