"""
Transparent overlay - test ile birebir ayni kurulum.
"""
import ctypes
import pygame
import OpenGL.GL as gl
import imgui
from imgui.integrations.pygame import PygameRenderer
import win32api, win32con, win32gui

from core.game import game

user32  = ctypes.WinDLL("user32",  use_last_error=True)
dwmapi  = ctypes.WinDLL("dwmapi")


class MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth",    ctypes.c_int),
                ("cxRightWidth",   ctypes.c_int),
                ("cyTopHeight",    ctypes.c_int),
                ("cyBottomHeight", ctypes.c_int)]


class OverlayWindow:
    def __init__(self):
        self.width  = 1920
        self.height = 1080
        self._renderer   = None
        self._running    = True
        self._hwnd       = None
        self._textures   = {}
        self._menu_was_open = False
        self._ex_base    = 0
        self._ex_passthru= 0

    def create(self, title: str = "CS2DMA"):
        self.width  = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        game.view.set_screen_size(float(self.width), float(self.height))

        pygame.init()
        pygame.display.set_caption(title)

        # Alpha destekli context - test ile ayni
        pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE,   8)
        pygame.display.gl_set_attribute(pygame.GL_RED_SIZE,     8)
        pygame.display.gl_set_attribute(pygame.GL_GREEN_SIZE,   8)
        pygame.display.gl_set_attribute(pygame.GL_BLUE_SIZE,    8)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE,   0)
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 0)

        pygame.display.set_mode(
            (self.width, self.height),
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.NOFRAME
        )

        self._hwnd = pygame.display.get_wm_info()["window"]

        # Extended style
        self._ex_base     = win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST
        self._ex_passthru = (self._ex_base |
                             win32con.WS_EX_TRANSPARENT |
                             win32con.WS_EX_NOACTIVATE)

        # Baslangicta pass-through (menu kapali)
        win32gui.SetWindowLong(self._hwnd, win32con.GWL_EXSTYLE, self._ex_passthru)

        # DWM seffaflik - test ile ayni
        dwmapi.DwmExtendFrameIntoClientArea(
            self._hwnd, ctypes.byref(MARGINS(-1, -1, -1, -1))
        )
        win32gui.SetLayeredWindowAttributes(
            self._hwnd, 0x000000, 0, win32con.LWA_COLORKEY
        )
        win32gui.SetWindowPos(
            self._hwnd, win32con.HWND_TOPMOST,
            0, 0, self.width, self.height,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
        )

        # OpenGL
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # imgui
        imgui.create_context()
        self._renderer = PygameRenderer()
        io = imgui.get_io()
        io.display_size = (self.width, self.height)
        self._load_font(io)
        self._apply_style()

        print(f"[ info ] Overlay {self.width}x{self.height}")

    # ------------------------------------------------------------------ menu toggle
    def _set_clickthrough(self, enabled: bool):
        if enabled:
            win32gui.SetWindowLong(self._hwnd, win32con.GWL_EXSTYLE, self._ex_passthru)
        else:
            win32gui.SetWindowLong(self._hwnd, win32con.GWL_EXSTYLE, self._ex_base)
            win32gui.SetWindowPos(
                self._hwnd, win32con.HWND_TOPMOST,
                0, 0, self.width, self.height,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )

    # ------------------------------------------------------------------ main loop
    def run(self, render_callback):
        from ui.menu import menu_config
        io    = imgui.get_io()
        clock = pygame.time.Clock()

        while self._running:
            menu_open = menu_config.show_menu

            if menu_open != self._menu_was_open:
                self._set_clickthrough(not menu_open)
                self._menu_was_open = menu_open

            if menu_open:
                mx, my = win32api.GetCursorPos()
                io.mouse_pos  = (float(mx), float(my))
                io.mouse_down[0] = bool(user32.GetAsyncKeyState(win32con.VK_LBUTTON)  & 0x8000)
                io.mouse_down[1] = bool(user32.GetAsyncKeyState(win32con.VK_RBUTTON)  & 0x8000)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print(f"[ info ] QUIT event - kapaniyor")
                    self._running = False
                elif event.type != pygame.NOEVENT:
                    pass  # diger eventler
                if menu_open:
                    self._renderer.process_event(event)

            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            imgui.new_frame()
            try:
                render_callback()
            except Exception as e:
                import traceback
                print(f"[ error ] render_callback: {e}")
                traceback.print_exc()
            imgui.render()
            draw_data = imgui.get_draw_data()
            if draw_data.valid:
                self._renderer.render(draw_data)
            pygame.display.flip()
            clock.tick(144)

        self._cleanup()

    def _cleanup(self):
        if self._renderer:
            self._renderer.shutdown()
        pygame.quit()

    # ------------------------------------------------------------------ texture
    def load_texture(self, path: str):
        if path in self._textures:
            return self._textures[path]
        try:
            from PIL import Image
            import numpy as np
            img  = Image.open(path).convert("RGBA")
            data = np.array(img, dtype=np.uint8)
            tid  = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, tid)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                            img.width, img.height, 0,
                            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
            self._textures[path] = tid
            return tid
        except Exception as e:
            print(f"[ texture ] {path}: {e}")
            return None

    # ------------------------------------------------------------------ font
    def _load_font(self, io):
        import os
        windir = os.environ.get("WINDIR", "C:\\Windows")
        for name in ("segoeui.ttf", "tahoma.ttf", "arial.ttf"):
            path = os.path.join(windir, "Fonts", name)
            if os.path.exists(path):
                try:
                    gr = imgui.GlyphRanges([
                        0x0020, 0x00FF,
                        0x011E, 0x011F,
                        0x0130, 0x0131,
                        0x015E, 0x015F,
                        0
                    ])
                    io.fonts.add_font_from_file_ttf(path, 15.0, glyph_ranges=gr)
                    print(f"[ font ] {name}")
                    return
                except Exception:
                    pass
        io.fonts.add_font_default()

    # ------------------------------------------------------------------ style
    def _apply_style(self):
        s = imgui.get_style()
        s.window_padding     = (15, 15)
        s.window_rounding    = 5.0
        s.frame_padding      = (5, 5)
        s.frame_rounding     = 4.0
        s.item_spacing       = (12, 8)
        s.item_inner_spacing = (8, 6)
        s.grab_min_size      = 5.0
        s.grab_rounding      = 3.0
        s.scrollbar_size     = 15.0

        c = s.colors
        c[imgui.COLOR_TEXT]                     = (0.80, 0.80, 0.83, 1.00)
        c[imgui.COLOR_TEXT_DISABLED]            = (0.24, 0.23, 0.29, 1.00)
        c[imgui.COLOR_WINDOW_BACKGROUND]        = (0.07, 0.06, 0.08, 0.95)
        c[imgui.COLOR_POPUP_BACKGROUND]         = (0.07, 0.07, 0.09, 1.00)
        c[imgui.COLOR_BORDER]                   = (0.80, 0.80, 0.83, 0.88)
        c[imgui.COLOR_FRAME_BACKGROUND]         = (0.10, 0.09, 0.12, 1.00)
        c[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (0.24, 0.23, 0.29, 1.00)
        c[imgui.COLOR_FRAME_BACKGROUND_ACTIVE]  = (0.56, 0.56, 0.58, 1.00)
        c[imgui.COLOR_TITLE_BACKGROUND]         = (0.10, 0.09, 0.12, 1.00)
        c[imgui.COLOR_TITLE_BACKGROUND_ACTIVE]  = (0.07, 0.07, 0.09, 1.00)
        c[imgui.COLOR_BUTTON]                   = (0.10, 0.09, 0.12, 1.00)
        c[imgui.COLOR_BUTTON_HOVERED]           = (0.24, 0.23, 0.29, 1.00)
        c[imgui.COLOR_BUTTON_ACTIVE]            = (0.56, 0.56, 0.58, 1.00)
        c[imgui.COLOR_HEADER]                   = (0.10, 0.09, 0.12, 1.00)
        c[imgui.COLOR_HEADER_HOVERED]           = (0.56, 0.56, 0.58, 1.00)
        c[imgui.COLOR_HEADER_ACTIVE]            = (0.06, 0.05, 0.07, 1.00)
        c[imgui.COLOR_CHECK_MARK]               = (0.80, 0.80, 0.83, 0.31)
        c[imgui.COLOR_SLIDER_GRAB]              = (0.80, 0.80, 0.83, 0.31)
        c[imgui.COLOR_SLIDER_GRAB_ACTIVE]       = (0.06, 0.05, 0.07, 1.00)
