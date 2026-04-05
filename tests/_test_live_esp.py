"""Live ESP test - entity oku + overlay'e ciz, 15 saniye."""
import os, sys, time, ctypes, struct, threading
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off

import pygame
import OpenGL.GL as gl
import imgui
from imgui.integrations.pygame import PygameRenderer
import win32api, win32con, win32gui

dwmapi = ctypes.WinDLL("dwmapi")

W = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
H = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
game.view.set_screen_size(float(W), float(H))

# ---- Entity guncelleme thread ----
entities = []
ent_lock = threading.Lock()

def update_loop():
    while True:
        game.update_matrix()
        game.update_entity_list_entry()
        ges = pm.read_u64(game.address.entity_list)
        entry_base = game.address.entity_list_entry
        ctrl_addr = pm.read_u64(game.address.local_controller)
        if not entry_base or not ges:
            time.sleep(0.05)
            continue

        tmp = []
        for chunk_idx in range(4):
            chunk_ptr = pm.read_u64(entry_base + chunk_idx * 0x8)
            if not chunk_ptr or chunk_ptr > 0x7FFFFFFFFFFF or chunk_ptr < 0x10000:
                continue
            for ent_idx in range(512):
                ctrl = pm.read_u64(chunk_ptr + ent_idx * 0x8)
                if not ctrl or ctrl > 0x7FFFFFFFFFFF or ctrl < 0x10000 or ctrl == ctrl_addr:
                    continue
                alive = pm.read_i32(ctrl + off.IsAlive)
                if alive != 1:
                    continue
                name_raw = pm.read_memory(ctrl + off.iszPlayerName, 32)
                name = ""
                if name_raw:
                    end = name_raw.find(b'\x00')
                    name = name_raw[:end].decode(errors="ignore") if end != -1 else ""
                if not name:
                    continue
                ph = pm.read_u32(ctrl + off.PlayerPawn)
                if not ph:
                    continue
                ci = (ph & 0x7FFF) >> 9
                ei = ph & 0x1FF
                ch = pm.read_u64(ges + 0x10 + 8 * ci)
                if not ch:
                    continue
                pawn = pm.read_u64(ch + 0x70 * ei)
                if not pawn or pawn > 0x7FFFFFFFFFFF or pawn < 0x10000:
                    continue
                hp = pm.read_i32(pawn + off.CurrentHealth)
                if hp <= 0:
                    continue
                pos = pm.read_vec3(pawn + off.Pos)
                scene = pm.read_u64(pawn + off.GameSceneNode)
                bone_arr = pm.read_u64(scene + off.BoneArray) if scene else 0
                head_pos = None
                if bone_arr:
                    raw_bone = pm.read_memory(bone_arr + 6 * 0x20, 12)
                    if raw_bone:
                        head_pos = struct.unpack_from("<fff", raw_bone)
                tmp.append((name, hp, pos, head_pos))

        with ent_lock:
            entities[:] = tmp
        time.sleep(0.016)

threading.Thread(target=update_loop, daemon=True).start()

# ---- Overlay ----
pygame.init()
pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE,   8)
pygame.display.gl_set_attribute(pygame.GL_RED_SIZE,     8)
pygame.display.gl_set_attribute(pygame.GL_GREEN_SIZE,   8)
pygame.display.gl_set_attribute(pygame.GL_BLUE_SIZE,    8)
pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE,   0)
pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 0)
pygame.display.set_mode((W, H), pygame.OPENGL | pygame.DOUBLEBUF | pygame.NOFRAME)
hwnd = pygame.display.get_wm_info()["window"]

ex = win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)

class MARGINS(ctypes.Structure):
    _fields_ = [("cxLeftWidth", ctypes.c_int), ("cxRightWidth", ctypes.c_int),
                ("cyTopHeight", ctypes.c_int), ("cyBottomHeight", ctypes.c_int)]
dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(MARGINS(-1,-1,-1,-1)))
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 0, win32con.LWA_COLORKEY)
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, W, H,
                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

gl.glClearColor(0.0, 0.0, 0.0, 0.0)
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

imgui.create_context()
renderer = PygameRenderer()
io = imgui.get_io()
io.display_size = (W, H)

clock = pygame.time.Clock()
start = time.time()
print(f"[ live esp ] {W}x{H} - 15 saniye")

while time.time() - start < 15.0:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break
        renderer.process_event(event)

    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    imgui.new_frame()

    dl = imgui.get_background_draw_list()
    wht = imgui.get_color_u32_rgba(1, 1, 1, 1)
    grn = imgui.get_color_u32_rgba(0, 1, 0, 1)
    red = imgui.get_color_u32_rgba(1, 0, 0, 1)

    with ent_lock:
        snap = list(entities)

    drawn = 0
    for name, hp, pos, head_pos in snap:
        foot = game.view.world_to_screen(pos)
        if foot is None:
            continue
        fx, fy = foot

        if head_pos:
            head = game.view.world_to_screen(head_pos)
        else:
            head = None

        hx = fx
        hy = fy - 80 if head is None else head[1]

        box_h = max(fy - hy, 10)
        box_w = box_h * 0.5
        x1 = fx - box_w / 2
        y1 = hy
        x2 = fx + box_w / 2
        y2 = fy

        if x2 < 0 or x1 > W or y2 < 0 or y1 > H:
            continue

        dl.add_rect(x1, y1, x2, y2, wht, 0, 0, 1.5)
        dl.add_text(x1, y1 - 14, wht, f"{name} {hp}HP")
        drawn += 1

    dl.add_text(10, 10, grn, f"Entity:{len(snap)} Drawn:{drawn} FPS:{clock.get_fps():.0f}")

    imgui.render()
    renderer.render(imgui.get_draw_data())
    pygame.display.flip()
    clock.tick(144)

renderer.shutdown()
pygame.quit()
print(f"[ live esp ] Bitti. Entity: {len(entities)}")
