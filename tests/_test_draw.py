"""Overlay cizim testi - arka plan seffaf, kutular gorunmeli."""
import os, sys, time, ctypes
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
import OpenGL.GL as gl
import imgui
from imgui.integrations.pygame import PygameRenderer
import win32api, win32con, win32gui, win32com.client

user32  = ctypes.WinDLL("user32")
dwmapi  = ctypes.WinDLL("dwmapi")

W = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
H = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

# SDL'ye alpha destekli OpenGL context iste
pygame.init()
# Alpha buffer icin SDL attribute'lari set et
pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)
pygame.display.gl_set_attribute(pygame.GL_RED_SIZE,   8)
pygame.display.gl_set_attribute(pygame.GL_GREEN_SIZE, 8)
pygame.display.gl_set_attribute(pygame.GL_BLUE_SIZE,  8)
pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 0)
pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 0)

pygame.display.set_mode((W, H), pygame.OPENGL | pygame.DOUBLEBUF | pygame.NOFRAME)
hwnd = pygame.display.get_wm_info()["window"]

# WS_EX_LAYERED + WS_EX_TOPMOST + WS_EX_TRANSPARENT (click-through)
ex = win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)

# DWM ile pencereyi tamamen seffaf yap (arka plan siyah olmaz)
# MARGINS: -1 tum alani blur/seffaf yapar
class MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth",    ctypes.c_int),
                ("cxRightWidth",   ctypes.c_int),
                ("cyTopHeight",    ctypes.c_int),
                ("cyBottomHeight", ctypes.c_int)]

margins = MARGINS(-1, -1, -1, -1)
dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

# Colorkey: siyah seffaf
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 0, win32con.LWA_COLORKEY)
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, W, H,
                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

# OpenGL: seffaf siyah ile temizle
gl.glClearColor(0.0, 0.0, 0.0, 0.0)
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

imgui.create_context()
renderer = PygameRenderer()
io = imgui.get_io()
io.display_size = (W, H)

clock = pygame.time.Clock()
start = time.time()
print(f"[ test ] {W}x{H} - 10 saniye, kutular gorunmeli, arka plan seffaf olmali")

while time.time() - start < 10.0:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break
        renderer.process_event(event)

    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    imgui.new_frame()

    dl = imgui.get_background_draw_list()
    red = imgui.get_color_u32_rgba(1, 0, 0, 1)
    grn = imgui.get_color_u32_rgba(0, 1, 0, 1)
    wht = imgui.get_color_u32_rgba(1, 1, 1, 1)
    yel = imgui.get_color_u32_rgba(1, 1, 0, 1)

    dl.add_rect(10, 10, 110, 110, red, 0, 0, 3)
    dl.add_text(15, 15, red, "SOL UST")
    dl.add_rect(W-110, 10, W-10, 110, grn, 0, 0, 3)
    dl.add_text(W-105, 15, grn, "SAG UST")

    cx, cy = W//2, H//2
    dl.add_rect(cx-50, cy-100, cx+50, cy+100, wht, 0, 0, 2)
    dl.add_text(cx-40, cy-115, wht, "ENEMY")
    dl.add_line(cx-10, cy, cx+10, cy, wht, 1)
    dl.add_line(cx, cy-10, cx, cy+10, wht, 1)
    dl.add_text(10, H-30, grn, f"FPS: {clock.get_fps():.0f}")

    imgui.render()
    renderer.render(imgui.get_draw_data())
    pygame.display.flip()
    clock.tick(144)

renderer.shutdown()
pygame.quit()
print("[ test ] Bitti")
