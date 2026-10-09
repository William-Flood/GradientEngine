# Code taken from https://github.com/AntonOvsyannikov/PyOpenGL_Examples_SaveToFile/blob/master/LibGL/Buffers.py

PFD_TYPE_RGBA =       0
PFD_TYPE_COLORINDEX = 1
PFD_MAIN_PLANE =      0
PFD_OVERLAY_PLANE =   1
PFD_UNDERLAY_PLANE =  (-1)
PFD_DOUBLEBUFFER =           0x00000001
PFD_STEREO =                 0x00000002
PFD_DRAW_TO_WINDOW =         0x00000004
PFD_DRAW_TO_BITMAP =         0x00000008
PFD_SUPPORT_GDI =            0x00000010
PFD_SUPPORT_OPENGL =         0x00000020
PFD_GENERIC_FORMAT =         0x00000040
PFD_NEED_PALETTE =           0x00000080
PFD_NEED_SYSTEM_PALETTE =    0x00000100
PFD_SWAP_EXCHANGE =          0x00000200
PFD_SWAP_COPY =              0x00000400
PFD_SWAP_LAYER_BUFFERS =     0x00000800
PFD_GENERIC_ACCELERATED =    0x00001000
PFD_DEPTH_DONTCARE =         0x20000000
PFD_DOUBLEBUFFER_DONTCARE =  0x40000000
PFD_STEREO_DONTCARE =        0x80000000

from OpenGL.WGL import *

from win32api import *
from win32con import *
from win32gui import *
import uuid
from ctypes import *

def CreateWindowA(wndProc = DefWindowProc, title = '', size = (300, 300), style = WS_OVERLAPPEDWINDOW, coords = (CW_USEDEFAULT, CW_USEDEFAULT)):
    sx, sy = size

    hInstance = GetModuleHandle(None)

    wndClass = WNDCLASS()

    wndClass.lpfnWndProc = wndProc
    wndClass.hInstance = hInstance
    wndClass.hbrBackground = GetStockObject(WHITE_BRUSH)
    wndClass.hCursor = LoadCursor(0, IDC_ARROW)
    wndClass.lpszClassName = str(uuid.uuid4())
    wndClass.style = CS_OWNDC

    wndClassAtom = RegisterClass(wndClass)

    return CreateWindow(wndClassAtom, title, style, coords[0], coords[1], size[0], size[1], 0, 0, hInstance, None)


# =========================================
# OpenGL context creation helpers

def CreateContext(hWnd, doubleBuffer = True, colorBits = 32, depthBits = 24, pixelType = PFD_TYPE_RGBA):
    pfd = PIXELFORMATDESCRIPTOR()

    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | (PFD_DOUBLEBUFFER if doubleBuffer else 0)
    pfd.iPixelType = pixelType
    pfd.cColorBits = colorBits
    pfd.cDepthBits = depthBits
    pfd.iLayerType = PFD_MAIN_PLANE

    hdc = GetDC(hWnd)

    pixelformat = ChoosePixelFormat(hdc, pfd)
    SetPixelFormat(hdc, pixelformat, pfd)

    oglrc = wglCreateContext(hdc)
    wglMakeCurrent(hdc, oglrc)

def DeleteContext():
    hrc = wglGetCurrentContext()
    wglMakeCurrent(0, 0)
    if hrc: wglDeleteContext(hrc)
    # check is context created succesfully
    # print "OpenGL version:", glGetString(GL_VERSION)