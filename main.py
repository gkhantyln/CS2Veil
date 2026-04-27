"""CS2Veil - main.py"""
import os, sys, time, struct, threading, math, ctypes
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---- Init ----
from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm

# CS2 acilana kadar bekle
import time as _t
while True:
    if pm.attach("cs2.exe"):
        break
    print("[ CS2Veil ] cs2.exe bekleniyor...", end="\r")
    _t.sleep(2.0)
print()  # Satir temizle
from core.game import game; game.init_address()
from core.offsets import offsets as off
from core.bone import BONEINDEX, BONE_JOINT_SIZE, BONE_CHAINS
from mods.aimbot import aim_config, HOTKEY_NAMES as AIM_HK, PISTOLS, SNIPERS, NO_RECOIL_WEAPONS
from mods.triggerbot import trigger_config, HOTKEY_NAMES as TRIG_HK
from utils.kmbox import kmbox; kmbox.init_from_config("kmbox.json")
from ui.menu import menu_config
from utils.config_manager import save_config, load_config, load_last_config, list_configs, delete_config
os.makedirs("config", exist_ok=True)

# Pre-compiled struct parsers — her çağrıda format string parse etme
_S_I32  = struct.Struct("<i")
_S_U32  = struct.Struct("<I")
_S_U64  = struct.Struct("<Q")
_S_F2   = struct.Struct("<ff")
_S_F3   = struct.Struct("<fff")
_S_F16  = struct.Struct("<16f")

def _i32(buf, o): return _S_I32.unpack_from(buf, o)[0]
def _u32(buf, o): return _S_U32.unpack_from(buf, o)[0]
def _u64(buf, o): return _S_U64.unpack_from(buf, o)[0]
def _f2(buf, o):  return _S_F2.unpack_from(buf, o)
def _f3(buf, o):  return _S_F3.unpack_from(buf, o)

import pygame, OpenGL.GL as gl, imgui
from imgui.integrations.pygame import PygameRenderer
import win32api, win32con, win32gui

user32 = ctypes.WinDLL("user32")
dwmapi = ctypes.WinDLL("dwmapi")

# Windows timer resolution 1ms — time.sleep(0.001) gerçekten 1ms uyur
ctypes.windll.winmm.timeBeginPeriod(1)

class MARGINS(ctypes.Structure):
    _fields_ = [("l",ctypes.c_int),("r",ctypes.c_int),("t",ctypes.c_int),("b",ctypes.c_int)]

W = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
H = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
game.view.set_screen_size(float(W), float(H))

# ---- Pygame / OpenGL ----
pygame.init()
for a,v in [(pygame.GL_ALPHA_SIZE,8),(pygame.GL_RED_SIZE,8),(pygame.GL_GREEN_SIZE,8),
            (pygame.GL_BLUE_SIZE,8),(pygame.GL_DEPTH_SIZE,0),(pygame.GL_STENCIL_SIZE,0)]:
    pygame.display.gl_set_attribute(a,v)
pygame.display.set_mode((W,H), pygame.OPENGL|pygame.DOUBLEBUF|pygame.NOFRAME)
hwnd = pygame.display.get_wm_info()["window"]

EX_PT = win32con.WS_EX_LAYERED|win32con.WS_EX_TOPMOST|win32con.WS_EX_TRANSPARENT|win32con.WS_EX_NOACTIVATE
EX_MN = win32con.WS_EX_LAYERED|win32con.WS_EX_TOPMOST
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, EX_PT)
dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(MARGINS(-1,-1,-1,-1)))
win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 0, win32con.LWA_COLORKEY)
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,W,H, win32con.SWP_SHOWWINDOW)

gl.glClearColor(0,0,0,0)
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

imgui.create_context()
renderer = PygameRenderer()
io = imgui.get_io(); io.display_size=(W,H)

for fn in ("segoeui.ttf","tahoma.ttf","arial.ttf"):
    fp=os.path.join(os.environ.get("WINDIR","C:/Windows"),"Fonts",fn)
    if os.path.exists(fp):
        try:
            gr=imgui.GlyphRanges([0x0020,0x00FF,0x011E,0x011F,0x0130,0x0131,0x015E,0x015F,0])
            io.fonts.add_font_from_file_ttf(fp,15.0,glyph_ranges=gr); print(f"[ font ] {fn}"); break
        except Exception: pass
else: io.fonts.add_font_default()

s=imgui.get_style(); s.window_rounding=5; s.frame_rounding=4; s.grab_rounding=3
c=s.colors
c[imgui.COLOR_TEXT]=(0.80,0.80,0.83,1); c[imgui.COLOR_WINDOW_BACKGROUND]=(0.07,0.06,0.08,0.95)
c[imgui.COLOR_FRAME_BACKGROUND]=(0.10,0.09,0.12,1); c[imgui.COLOR_BUTTON]=(0.10,0.09,0.12,1)
c[imgui.COLOR_TITLE_BACKGROUND]=(0.10,0.09,0.12,1); c[imgui.COLOR_TITLE_BACKGROUND_ACTIVE]=(0.07,0.07,0.09,1)
c[imgui.COLOR_HEADER]=(0.10,0.09,0.12,1); c[imgui.COLOR_CHECK_MARK]=(0.80,0.80,0.83,0.31)
c[imgui.COLOR_SLIDER_GRAB]=(0.80,0.80,0.83,0.31); c[imgui.COLOR_BORDER]=(0.80,0.80,0.83,0.88)
c[imgui.COLOR_FRAME_BACKGROUND_HOVERED]=(0.24,0.23,0.29,1); c[imgui.COLOR_FRAME_BACKGROUND_ACTIVE]=(0.56,0.56,0.58,1)
c[imgui.COLOR_BUTTON_HOVERED]=(0.24,0.23,0.29,1); c[imgui.COLOR_BUTTON_ACTIVE]=(0.56,0.56,0.58,1)
c[imgui.COLOR_HEADER_HOVERED]=(0.56,0.56,0.58,1); c[imgui.COLOR_HEADER_ACTIVE]=(0.06,0.05,0.07,1)
c[imgui.COLOR_SLIDER_GRAB_ACTIVE]=(0.06,0.05,0.07,1)

# CS2 penceresini bul
def _find_cs2():
    r=[]
    def cb(h,_):
        if win32gui.IsWindowVisible(h):
            t=win32gui.GetWindowText(h)
            if "counter-strike" in t.lower(): r.append(h)
        return True
    win32gui.EnumWindows(cb,None)
    return r[0] if r else None

cs2h = _find_cs2()
if cs2h:
    rx,ry,rx2,ry2=win32gui.GetWindowRect(cs2h)
    rw,rh=rx2-rx,ry2-ry
    if rw>0 and rh>0:
        W,H=rw,rh; game.view.set_screen_size(float(W),float(H)); io.display_size=(W,H)
        win32gui.SetWindowPos(hwnd,win32con.HWND_TOPMOST,rx,ry,rw,rh,win32con.SWP_SHOWWINDOW)
        print(f"[ info ] CS2: {rx},{ry} {rw}x{rh}")
    win32gui.SetWindowPos(cs2h,win32con.HWND_NOTOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
else:
    print("[ warn ] CS2 penceresi bulunamadi")

print(f"[ CS2Veil ] Overlay {W}x{H} | INSERT=menu")

def _apply_stream_proof(enabled: bool):
    """OBS/ekran paylasiminda overlay'i gizle — Win10 2004+"""
    try:
        val = 0x11 if enabled else 0  # WDA_EXCLUDEFROMCAPTURE = 0x11
        user32.SetWindowDisplayAffinity(hwnd, val)
    except Exception:
        pass

# Son kaydedilen config'i yukle
try:
    if load_last_config(menu_config, aim_config, trigger_config, None):
        print("[ config ] Son config yuklendi")
        if menu_config.stream_proof:
            _apply_stream_proof(True)
except Exception as _e:
    print(f"[ config ] Yuklenemedi: {_e}")

# ---- Entity thread ----
_ents, _local, _lock = [], None, threading.Lock()

def _read_weapon(pawn):
    # pClippingWeapon -> +0x10 -> +0x20 -> weapon name string
    p1 = pm.read_u64(pawn + off.pClippingWeapon)
    if not p1 or p1 > 0x7FFFFFFFFFFF: return ""
    p2 = pm.read_u64(p1 + 0x10)
    if not p2 or p2 > 0x7FFFFFFFFFFF: return ""
    p3 = pm.read_u64(p2 + 0x20)
    if not p3 or p3 > 0x7FFFFFFFFFFF: return ""
    r = pm.read_memory(p3, 32)
    if not r: return ""
    e = r.find(b'\x00'); n = r[:e].decode(errors="ignore") if e != -1 else ""
    i = n.find("_"); return n[i+1:] if i != -1 else n

def _w2s_snapshot(m, sw2, sh2, pos):
    """Matrix snapshot ile world_to_screen — lock yok, entity loop'ta kullanılır."""
    x, y, z = pos
    W = m[3][0]*x + m[3][1]*y + m[3][2]*z + m[3][3]
    if abs(W) <= 0.001:
        return None
    # W negatifse arkada demek — None döndür
    if W < 0:
        return None
    sx = sw2 + (m[0][0]*x + m[0][1]*y + m[0][2]*z + m[0][3]) / W * sw2
    sy = sh2 - (m[1][0]*x + m[1][1]*y + m[1][2]*z + m[1][3]) / W * sh2
    if not (math.isfinite(sx) and math.isfinite(sy)):
        return None
    if abs(sx) > sw2 * 20 or abs(sy) > sh2 * 20:
        return None
    return (sx, sy)

def _read_bones(pawn_buf, pawn, m_snap, sw2, sh2):
    """
    Bone'ları entity loop'ta okur ve screen koordinatlarını burada hesaplar.
    Matrix snapshot dışarıdan verilir — lock yok, render thread beklenmez.
    """
    sc_off = off.GameSceneNode
    sc = _u64(pawn_buf, sc_off) if sc_off + 8 <= len(pawn_buf) else pm.read_u64(pawn + sc_off)
    if not sc or sc > 0x7FFFFFFFFFFF or sc < 0x10000:
        return []
    ba = pm.read_u64(sc + off.BoneArray)
    if not ba or ba > 0x7FFFFFFFFFFF or ba < 0x10000:
        return []
    r = pm.read_memory(ba, 32 * BONE_JOINT_SIZE)
    if not r:
        return []

    out = []
    for i in range(32):
        o = i * BONE_JOINT_SIZE
        if o + 12 > len(r):
            break
        x, y, z = _f3(r, o)
        W = m_snap[3][0]*x + m_snap[3][1]*y + m_snap[3][2]*z + m_snap[3][3]
        if W > 0.001:
            sx = sw2 + (m_snap[0][0]*x + m_snap[0][1]*y + m_snap[0][2]*z + m_snap[0][3]) / W * sw2
            sy = sh2 - (m_snap[1][0]*x + m_snap[1][1]*y + m_snap[1][2]*z + m_snap[1][3]) / W * sh2
            scr = (sx, sy) if (math.isfinite(sx) and math.isfinite(sy)
                               and abs(sx) < sw2 * 20
                               and abs(sy) < sh2 * 20) else None
        else:
            scr = None
        out.append({"pos": (x, y, z), "screen": scr})
    return out

def _entity_loop():
    global _ents,_local
    last_entry_update = 0
    last_weapon_update = 0
    _weapon_cache = {}
    _rcs_old_punch_p = 0.0
    _rcs_old_punch_y = 0.0
    while True:
        try:
            # Matrix güncelle ve snapshot al — iterasyon boyunca tek lock
            game.address.matrix = game.address.client_dll + off.Matrix
            game.update_matrix()
            with game.view._matrix_lock:
                m_snap = [row[:] for row in game.view.matrix]
            # Dogrulama: m_snap[0][0] sifir ise matrix gecersiz
            if abs(m_snap[0][0]) < 0.0001 and abs(m_snap[1][1]) < 0.0001:
                time.sleep(0.005); continue
            sw2 = game.view.screen_w / 2
            sh2 = game.view.screen_h / 2
            now = time.monotonic()

            # Entity list entry her saniye guncelle
            if now - last_entry_update > 1.0:
                game.update_entity_list_entry()
                last_entry_update = now
            ges=pm.read_u64(game.address.entity_list)
            base=game.address.entity_list_entry
            lc=pm.read_u64(game.address.local_controller)
            lp=pm.read_u64(game.address.local_pawn)

            # lp 0 ise controller'dan handle yoluyla bulmayı dene
            if not lp and lc:
                ph = pm.read_u32(lc + off.PlayerPawn)
                if ph:
                    ges_ptr = pm.read_u64(game.address.entity_list)
                    if ges_ptr:
                        c2 = (ph & 0x7FFF) >> 9
                        e2 = ph & 0x1FF
                        ch = pm.read_u64(ges_ptr + 0x10 + 8 * c2)
                        if ch:
                            lp_try = pm.read_u64(ch + 0x70 * e2)
                            if lp_try and 0x10000 < lp_try < 0x7FFFFFFFFFFF:
                                lp = lp_try

            if not all([ges, base, lc]):
                if not base:
                    game.update_entity_list_entry()
                    last_entry_update = time.monotonic()
                time.sleep(0.05); continue
            cs = pm.read_u64(lp + off.CameraServices) if lp else 0
            lp_buf = pm.read_pawn_block(lp) if lp else None
            if lp_buf:
                pp_raw = _f2(lp_buf, off.aimPunchAngle) if off.aimPunchAngle < 0x4000 else (0.0, 0.0)
                loc={"ctrl":lc,"pawn":lp,
                     "team":_i32(lp_buf, off.TeamID),
                     "hp":  _i32(lp_buf, off.CurrentHealth),
                     "pos": _f3(lp_buf,  off.Pos),
                     "ang": _f2(lp_buf,  off.angEyeAngles),
                     "cam": _f3(lp_buf,  off.vecLastClipCameraPos),
                     "punch": pp_raw,
                     "fov": pm.read_i32(cs+off.iFovStart) if cs else 90,
                     "weapon":_read_weapon(lp),"idx":0}
            else:
                # lp yoksa controller'dan temel bilgileri al
                loc={"ctrl":lc,"pawn":lp,
                     "team":pm.read_i32(lc+off.TeamID) if lc else 0,
                     "hp":  pm.read_i32(lp+off.CurrentHealth) if lp else 100,
                     "pos": pm.read_vec3(lp+off.Pos) if lp else (0.0,0.0,0.0),
                     "ang": pm.read_vec2(lp+off.angEyeAngles) if lp else (0.0,0.0),
                     "cam": pm.read_vec3(lp+off.vecLastClipCameraPos) if lp else (0.0,0.0,0.0),
                     "punch": (0.0,0.0),
                     "fov": pm.read_i32(cs+off.iFovStart) if cs else 90,
                     "weapon":"","idx":0}
            tmp=[]
            for ci in range(4):
                cp=pm.read_u64(base+ci*0x8)
                if not cp or cp>0x7FFFFFFFFFFF or cp<0x10000: continue
                for ei in range(512):
                    ctrl=pm.read_u64(cp+ei*0x8)
                    if not ctrl or ctrl>0x7FFFFFFFFFFF or ctrl<0x10000: continue
                    if ctrl==lc: loc["idx"]=ci*512+ei; continue
                    if pm.read_i32(ctrl+off.IsAlive)!=1: continue
                    nr=pm.read_memory(ctrl+off.iszPlayerName,32)
                    if not nr: continue
                    e2=nr.find(b'\x00'); name=nr[:e2].decode(errors="ignore") if e2!=-1 else ""
                    if not name: continue
                    team=pm.read_i32(ctrl+off.TeamID)
                    ph=pm.read_u32(ctrl+off.PlayerPawn)
                    if not ph: continue
                    c2=(ph&0x7FFF)>>9; e3=ph&0x1FF
                    ch=pm.read_u64(ges+0x10+8*c2)
                    if not ch: continue
                    pawn=pm.read_u64(ch+0x70*e3)
                    if not pawn or pawn>0x7FFFFFFFFFFF or pawn<0x10000: continue

                    # Pawn batch okuma — tek ReadProcessMemory ile tüm netvars
                    pawn_buf = pm.read_pawn_block(pawn)
                    if not pawn_buf: continue

                    hp = _i32(pawn_buf, off.CurrentHealth)
                    if hp<=0: continue

                    pos = _f3(pawn_buf, off.Pos)
                    ang = _f2(pawn_buf, off.angEyeAngles)
                    vel = _f3(pawn_buf, off.vecVelocity) if off.vecVelocity else (0.0, 0.0, 0.0)
                    flags = _i32(pawn_buf, off.fFlags) if off.fFlags and off.fFlags < len(pawn_buf) - 4 else 0

                    # Weapon name: cache ile seyrek oku (500ms)
                    wpn = _weapon_cache.get(pawn, "")
                    if now - last_weapon_update > 0.5:
                        wpn = _read_weapon(pawn)
                        _weapon_cache[pawn] = wpn

                    # Bones: entity loop'ta matrix snapshot ile screen hesapla
                    bones = _read_bones(pawn_buf, pawn, m_snap, sw2, sh2)

                    # Eye ray endpoint — entity loop'ta hesapla
                    eye_end = None
                    if len(bones) > BONEINDEX.head and bones[BONEINDEX.head]["pos"]:
                        hx, hy, hz = bones[BONEINDEX.head]["pos"]
                        ep, ey2 = ang[0]*math.pi/180, ang[1]*math.pi/180
                        ll = math.cos(ep) * 50
                        eye_end = _w2s_snapshot(m_snap, sw2, sh2,
                                                (hx + math.cos(ey2)*ll,
                                                 hy + math.sin(ey2)*ll,
                                                 hz - math.sin(ep)*50))

                    # foot: ankle bone'dan, yoksa pos'tan — entity loop'ta hesapla
                    foot = None
                    for ai in (BONEINDEX.ankle_L, BONEINDEX.ankle_R):
                        if len(bones) > ai and bones[ai]["screen"]:
                            foot = bones[ai]["screen"]; break
                    if foot is None:
                        foot = _w2s_snapshot(m_snap, sw2, sh2, pos)

                    # quick_screen: pos'un ekran koordinatı — on eleme için
                    quick_screen = foot if foot else _w2s_snapshot(m_snap, sw2, sh2, pos)

                    # spotted mask — visibility check için
                    spotted = 0
                    if off.bSpottedByMask and off.bSpottedByMask + 8 <= len(pawn_buf):
                        spotted = _u64(pawn_buf, off.bSpottedByMask) if off.bSpottedByMask < len(pawn_buf) - 7 else 0

                    tmp.append({"ctrl":ctrl,"pawn":pawn,"name":name,"team":team,"hp":hp,
                                "pos":pos,"ang":ang,"vel":vel,"weapon":wpn,"bones":bones,
                                "foot":foot,"quick_screen":quick_screen,"eye_end":eye_end,
                                "spotted":spotted,"flags":flags})
            with _lock: _ents=tmp; _local=loc

            if now - last_weapon_update > 0.5:
                last_weapon_update = now
                # Sadece aktif pawn adreslerini cache'de tut
                active_pawns = {e["pawn"] for e in tmp}
                for k in list(_weapon_cache.keys()):
                    if k not in active_pawns:
                        del _weapon_cache[k]

            # No Flash: flash duration'i sifirla veya sinirla
            if menu_config.no_flash:                # Tamamen kapat
                pm.write_memory(lp + off.flFlashDuration, struct.pack("<f", 0.0))
            elif menu_config.flash_max_alpha < 255:
                # Flash alpha sinirla: flFlashDuration max degerini kisalt
                cur_flash = pm.read_float(lp + off.flFlashDuration) if hasattr(pm, 'read_float') else 0
                # flash_max_alpha: 255=hic, 0=tam -> duration max = (255-alpha)/255 * 3.5
                max_dur = (255 - menu_config.flash_max_alpha) / 255.0 * 3.5
                raw_flash = pm.read_memory(lp + off.flFlashDuration, 4)
                if raw_flash:
                    cur = struct.unpack_from("<f", raw_flash)[0]
                    if cur > max_dur:
                        pm.write_memory(lp + off.flFlashDuration, struct.pack("<f", max_dur))

            # BHop: Space basili + yerde ise zipla (SendInput ile)
            if menu_config.bhop_enabled and lp_buf:
                if user32.GetAsyncKeyState(0x20) & 0x8000:  # VK_SPACE
                    _flags = _i32(lp_buf, off.fFlags) if off.fFlags and off.fFlags < 0x4000 else 0
                    if _flags & 0x1:  # FL_ONGROUND = 1 — yerdeyse zıpla
                        # Space key up + down simüle et
                        _ki = (ctypes.c_uint32 * 1)(0x20)
                        user32.keybd_event(0x20, 0, 0x0002, 0)  # KEYUP
                        user32.keybd_event(0x20, 0, 0x0000, 0)  # KEYDOWN

        except Exception: pass
        time.sleep(0.005)  # ~200Hz — matrix + entity okuma ağır

threading.Thread(target=_entity_loop, daemon=True, name="cs2veil-entity").start()

# ── Aim loop — ~1000Hz, ayrı thread (externalv2 mimarisi) ────────────────────
def _norm_angle(a: float) -> float:
    while a >  180.0: a -= 360.0
    while a < -180.0: a += 360.0
    return a

def _aim_loop():
    """~1000Hz aim loop — tüm özellikler optimize edilmiş."""
    from mods.aimbot import SPRAY_PATTERNS
    from core.bone import AIM_BONE_INDEX as _ABI

    _prev_vel:    dict  = {}
    _locked_pawn: int   = 0
    _lock_lost_t: float = 0.0
    LOCK_GRACE          = 0.2

    _fallback = {
        BONEINDEX.head:    [BONEINDEX.neck_0, BONEINDEX.spine_3, BONEINDEX.spine_2],
        BONEINDEX.neck_0:  [BONEINDEX.spine_3, BONEINDEX.spine_2],
        BONEINDEX.spine_3: [BONEINDEX.spine_2, BONEINDEX.spine_1],
        BONEINDEX.spine_2: [BONEINDEX.spine_1, BONEINDEX.pelvis],
        BONEINDEX.spine_1: [BONEINDEX.pelvis],
        BONEINDEX.pelvis:  [],
    }

    while True:
        try:
            if not aim_config.enabled or not aim_config.hotkey:
                time.sleep(0.005); continue

            hk_down = bool(user32.GetAsyncKeyState(aim_config.hotkey) & 0x8000)
            if not hk_down:
                _prev_vel.clear()
                _locked_pawn = 0
                time.sleep(0.001); continue

            # Ateş ederken dur
            if aim_config.ignore_on_shot and bool(user32.GetAsyncKeyState(0x01) & 0x8000):
                time.sleep(0.001); continue

            with _lock:
                entities = list(_ents)
                local    = _local

            if not local:
                time.sleep(0.001); continue

            wpn_local = local.get("weapon", "")
            if wpn_local in NO_RECOIL_WEAPONS:
                time.sleep(0.001); continue

            lp = local.get("pawn")
            if not lp or not game.address.view_angle:
                time.sleep(0.001); continue

            # Taze okumalar — 3 RPM
            cam_raw = pm.read_memory(lp + off.vecLastClipCameraPos, 12)
            if not cam_raw or len(cam_raw) < 12:
                time.sleep(0.001); continue
            cam_x, cam_y, cam_z = _S_F3.unpack(cam_raw)
            if cam_x == 0.0 and cam_y == 0.0:
                pos_raw = pm.read_memory(lp + off.Pos, 12)
                if pos_raw and len(pos_raw) == 12:
                    cam_x, cam_y, cam_z = _S_F3.unpack(pos_raw)

            punch_raw = pm.read_memory(lp + off.aimPunchAngle, 8) if off.aimPunchAngle else b""
            punch_p, punch_y = _S_F2.unpack(punch_raw) if len(punch_raw) == 8 else (0.0, 0.0)

            va_raw = pm.read_memory(game.address.view_angle, 8)
            if not va_raw or len(va_raw) < 8:
                time.sleep(0.001); continue
            cur_p, cur_y = _S_F2.unpack(va_raw)

            shots_raw = pm.read_memory(lp + off.iShotsFired, 4) if off.iShotsFired else b""
            shots_fired = _S_U32.unpack(shots_raw)[0] if len(shots_raw) == 4 else 0

            local_team = local.get("team", 0)
            now_t      = time.monotonic()

            best_dist  = float("inf")
            best_new_p = None
            best_new_y = None
            best_pawn  = 0

            for ent in entities:
                if ent.get("hp", 0) <= 0:
                    continue
                if menu_config.team_check and local_team >= 2 and ent["team"] == local_team:
                    continue

                pawn_addr = ent.get("pawn", 0)
                bones     = ent["bones"]

                if len(bones) <= BONEINDEX.head or not bones[BONEINDEX.head]["pos"]:
                    continue

                hx, hy, hz = bones[BONEINDEX.head]["pos"]
                dx = hx - cam_x; dy = hy - cam_y
                d2 = math.sqrt(dx * dx + dy * dy)
                if d2 < 0.001: continue

                t_yaw   =  math.atan2(dy, dx) * 57.295779513
                t_pitch = -math.atan2(hz - cam_z, d2) * 57.295779513
                d_yaw   = _norm_angle(t_yaw   - cur_y)
                d_pitch = _norm_angle(t_pitch - cur_p)
                dist    = math.sqrt(d_yaw * d_yaw + d_pitch * d_pitch)

                # Target lock
                if aim_config.target_lock and _locked_pawn and pawn_addr == _locked_pawn:
                    if dist >= aim_config.fov:
                        if now_t - _lock_lost_t > LOCK_GRACE:
                            _locked_pawn = 0
                        else:
                            dist *= 0.1
                    else:
                        _lock_lost_t = now_t
                elif dist >= aim_config.fov:
                    continue

                if dist >= best_dist:
                    continue

                best_dist = dist
                best_pawn = pawn_addr

                # Hedef bone seç
                wpn = ent.get("weapon", "")
                if wpn in PISTOLS:
                    preferred = _ABI[min(aim_config.position_pistol, len(_ABI)-1)]
                elif wpn in SNIPERS:
                    preferred = _ABI[min(aim_config.position_sniper, len(_ABI)-1)]
                else:
                    preferred = _ABI[min(aim_config.position, len(_ABI)-1)]

                # Dinamik bone fallback
                bidx = None
                for candidate in [preferred] + _fallback.get(preferred, []):
                    if len(bones) > candidate and bones[candidate]["pos"]:
                        if bones[candidate]["screen"] is not None:
                            bidx = candidate; break
                if bidx is None:
                    for candidate in [preferred] + _fallback.get(preferred, []):
                        if len(bones) > candidate and bones[candidate]["pos"]:
                            bidx = candidate; break
                if bidx is None:
                    continue

                bx, by, bz = bones[bidx]["pos"]
                if bidx == BONEINDEX.head:
                    bz -= 1.0

                # Hız + ivme tahmini
                if aim_config.velocity_pred:
                    vx, vy, vz = ent.get("vel", (0.0, 0.0, 0.0))
                    ax = ay = az = 0.0
                    if pawn_addr in _prev_vel:
                        pvx, pvy, pvz, pt = _prev_vel[pawn_addr]
                        dt = now_t - pt
                        if 0 < dt < 0.1:
                            ax = max(-3000.0, min(3000.0, (vx - pvx) / dt))
                            ay = max(-3000.0, min(3000.0, (vy - pvy) / dt))
                    _prev_vel[pawn_addr] = (vx, vy, vz, now_t)
                    if abs(vx) < 500 and abs(vy) < 500 and (abs(vx) + abs(vy)) > 0.1:
                        pt_v = 0.015625 * 2.5
                        bx += vx * pt_v + ax * pt_v * pt_v * 0.5
                        by += vy * pt_v + ay * pt_v * pt_v * 0.5

                # Çömelme tahmini — flags bit 2 = ducking
                if aim_config.crouch_pred:
                    flags = ent.get("flags", 0)
                    if flags & 0x2:  # FL_DUCKING
                        bz -= 18.0  # çömelince kafa ~18 birim aşağı iner

                dx2 = bx - cam_x; dy2 = by - cam_y; dz2 = bz - cam_z
                d2b = math.sqrt(dx2 * dx2 + dy2 * dy2)
                if d2b < 0.001: continue

                t_yaw2   =  math.atan2(dy2, dx2) * 57.295779513
                t_pitch2 = -math.atan2(dz2, d2b) * 57.295779513

                d_yaw2   = _norm_angle(t_yaw2   - cur_y)
                d_pitch2 = _norm_angle(t_pitch2 - cur_p)

                # Smooth
                sm = aim_config.smooth
                if sm > 0.0:
                    dist_ratio = min(1.0, math.sqrt(d_yaw2**2 + d_pitch2**2) / max(aim_config.fov, 0.1))
                    sm = sm * (1.0 - dist_ratio * 0.8)
                    sm = max(0.01, min(sm, 0.99))

                best_new_p = cur_p + d_pitch2 * (1.0 - sm)
                best_new_y = cur_y + d_yaw2   * (1.0 - sm)

            if best_new_p is None:
                time.sleep(0.001); continue

            # RCS aim loop'ta değil, entity loop'ta çalışıyor
            # (aim tuşundan bağımsız, sol tık basılıyken aktif)

            # Spray pattern: sol tık basılıyken pattern kompansasyonu
            if aim_config.spray_control and bool(user32.GetAsyncKeyState(0x01) & 0x8000):
                _wpn_sp = local.get("weapon", "")
                if _wpn_sp in SPRAY_PATTERNS and shots_fired > 0:
                    pattern = SPRAY_PATTERNS[_wpn_sp]
                    sidx = min(max(shots_fired - 1, 0), len(pattern) - 1)
                    sp_p, sp_y = pattern[sidx]
                    best_new_p -= sp_p * aim_config.rcs_scale
                    best_new_y += sp_y * aim_config.rcs_scale

            if aim_config.target_lock and best_pawn:
                _locked_pawn = best_pawn
                _lock_lost_t = now_t

            best_new_p = max(-89.0, min(89.0, best_new_p))
            pm.write_memory(game.address.view_angle,
                            struct.pack("<ff", best_new_p, best_new_y))

            # Aim oturunca ateş et
            if aim_config.shot_timing:
                # Hedefle kalan açı farkı eşiğin altındaysa ateş et
                aim_err = math.sqrt(
                    _norm_angle(best_new_p - cur_p)**2 +
                    _norm_angle(best_new_y - cur_y)**2
                )
                if aim_err < aim_config.shot_threshold:
                    _triggerbot_shoot()
            elif aim_config.auto_shot:
                _triggerbot_shoot()

        except Exception as _e:
            pass

        time.sleep(0.001)  # ~1000Hz

        time.sleep(0.001)  # ~1000Hz

threading.Thread(target=_aim_loop, daemon=True, name="cs2veil-aim").start()

# ── RCS Thread — ~1000Hz, aim loop'tan bağımsız ──────────────────────────────
def _rcs_loop():
    """RCS: punch delta'sını ~1000Hz'de viewangle'a uygular."""
    _old_p = 0.0
    _old_y = 0.0
    while True:
        try:
            if not aim_config.rcs_enabled:
                _old_p = 0.0; _old_y = 0.0
                time.sleep(0.005); continue

            if not bool(user32.GetAsyncKeyState(0x01) & 0x8000):
                _old_p = 0.0; _old_y = 0.0
                time.sleep(0.001); continue

            with _lock:
                local = _local
            if not local:
                time.sleep(0.001); continue

            wpn = local.get("weapon", "")
            if wpn in NO_RECOIL_WEAPONS:
                time.sleep(0.001); continue

            lp = local.get("pawn")
            if not lp or not off.aimPunchAngle or not game.address.view_angle:
                time.sleep(0.001); continue

            punch_raw = pm.read_memory(lp + off.aimPunchAngle, 8)
            if not punch_raw or len(punch_raw) < 8:
                time.sleep(0.001); continue
            pp, py = _S_F2.unpack(punch_raw)

            dp = pp - _old_p
            dy = py - _old_y

            if abs(dp) > 0.001 or abs(dy) > 0.001:
                va_raw = pm.read_memory(game.address.view_angle, 8)
                if va_raw and len(va_raw) == 8:
                    cur_p, cur_y = _S_F2.unpack(va_raw)
                    new_p = max(-89.0, min(89.0, cur_p + dp * 2.0 * aim_config.rcs_scale))
                    new_y = cur_y + dy * 2.0 * aim_config.rcs_scale
                    pm.write_memory(game.address.view_angle,
                                    struct.pack("<ff", new_p, new_y))
            _old_p = pp
            _old_y = py

        except Exception:
            pass
        time.sleep(0.001)  # ~1000Hz

threading.Thread(target=_rcs_loop, daemon=True, name="cs2veil-rcs").start()

# ---- Config UI state ----
_cfg_name_buf   = [""]
_cfg_selected   = [-1]
_cfg_msg        = [""]
_cfg_msg_time   = [0.0]

# ---- Triggerbot yardimci fonksiyonlar ----
import ctypes.wintypes as _wt

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx",_wt.LONG),("dy",_wt.LONG),("mouseData",_wt.DWORD),
                ("dwFlags",_wt.DWORD),("time",_wt.DWORD),
                ("dwExtraInfo",ctypes.POINTER(ctypes.c_ulong))]
class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi",_MOUSEINPUT)]
class _INPUT(ctypes.Structure):
    _fields_ = [("type",_wt.DWORD),("_input",_INPUT_UNION)]

_last_shot_time = 0.0

def _do_click():
    """Sol tik - SendInput (CS2 mouse button icin raw input kullanmaz)."""
    for flag in (0x0002, 0x0004):  # LEFTDOWN, LEFTUP
        inp = _INPUT(); inp.type = 0
        inp._input.mi.dwFlags = flag
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def _triggerbot_shoot():
    """Oto ates - gecikme kontrollu."""
    global _last_shot_time
    now = time.monotonic()
    if now - _last_shot_time < trigger_config.delay_ms / 1000.0:
        return
    if bool(user32.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000):
        return  # Zaten basili
    _do_click()
    _last_shot_time = now

def _triggerbot_check(local, ents):
    """
    Crosshair'daki entity'yi bul:
    Ekran merkezine en yakin entity'nin head/neck bone'u
    merkeze cok yakinsa (triggerbot esigi) ates et.
    """
    global _last_shot_time
    now = time.monotonic()
    if now - _last_shot_time < trigger_config.delay_ms / 1000.0:
        return
    if bool(user32.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000):
        return

    lt = local["team"]
    cx, cy = W/2, H/2
    # Crosshair esigi: ekranin %2'si kadar piksel
    threshold = W * 0.02

    for ent in ents:
        if menu_config.team_check and lt >= 2 and ent["team"] == lt:
            continue
        bones = ent["bones"]
        # Head veya neck bone ekran merkezine yakin mi?
        for bidx in [BONEINDEX.head, BONEINDEX.neck_0]:
            if len(bones) <= bidx or not bones[bidx]["screen"]:
                continue
            sx, sy = bones[bidx]["screen"]
            dist = math.sqrt((sx-cx)**2 + (sy-cy)**2)
            if dist < threshold:
                _do_click()
                _last_shot_time = now
                return

# ---- Main loop ----
clock=pygame.time.Clock(); menu_open=False; mk_last=False; mk_t=0.0; menu_was=False

# HP'ye gore renk: tam HP'de kullanicinin secimi, dusunce kirmiziya kayar
def hp_color(hp, base_color, alpha=1.0):
    t = max(0.0, min(1.0, hp / 100.0))
    br, bg, bb = base_color[0], base_color[1], base_color[2]
    r = br * t + 1.0 * (1.0 - t)
    g = bg * t + 0.0 * (1.0 - t)
    b = bb * t + 0.0 * (1.0 - t)
    return imgui.get_color_u32_rgba(r, g, b, alpha)

# Crosshair state
_dyn_cross_size = 8.0

def draw_crosshair(dl, local, ents):
    """Crosshair ozellikleri: recoil, sniper, dynamic (glow'lu), snaplines."""
    global _dyn_cross_size
    if not local:
        return
    cx, cy = W / 2.0, H / 2.0

    # ── Snap Lines ───────────────────────────────────────────────────────
    if menu_config.crosshair_snaplines:
        sr, sg, sb, sa = menu_config.crosshair_snaplines_color
        lt = local["team"]
        for ent in ents:
            if menu_config.team_check and lt >= 2 and ent["team"] == lt:
                continue
            foot = ent.get("foot")
            if not foot:
                continue
            fx, fy = foot
            col = imgui.get_color_u32_rgba(sr, sg, sb, sa)
            dl.add_line(cx, H, fx, fy, col, 1.2)
            dl.add_circle_filled(fx, fy, 2.5, col)

    # ── Dış Oklar ────────────────────────────────────────────────────────
    if menu_config.crosshair_arrows:
        ar, ag, ab, aa = menu_config.crosshair_arrows_color
        lt = local["team"]
        arrow_len  = 8.0
        arrow_wing = 3.0

        for ent in ents:
            if menu_config.team_check and lt >= 2 and ent["team"] == lt:
                continue
            hp   = ent["hp"]
            foot = ent.get("foot")
            if not foot:
                continue
            fx, fy = foot

            # Ekran merkezinden düşmanın ayağına yön vektörü
            dx = fx - cx
            dy = fy - cy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 1.0:
                continue
            nx, ny = dx / dist, dy / dist  # normalize

            # Ok ucu: düşmanın ayağından biraz önce
            offset = 18.0  # ayaktan ne kadar uzakta
            tip_x = fx - nx * offset
            tip_y = fy - ny * offset

            # Ok kuyruğu
            base_x = tip_x - nx * arrow_len
            base_y = tip_y - ny * arrow_len

            # Kanatlar (perpendicular)
            px, py = -ny, nx
            lx2 = base_x + px * arrow_wing
            ly2 = base_y + py * arrow_wing
            rx2 = base_x - px * arrow_wing
            ry2 = base_y - py * arrow_wing

            # HP'ye göre renk
            t = max(0.0, min(1.0, hp / 100.0))
            fr = ar * t + 1.0 * (1.0 - t)
            fg = ag * t + 0.0 * (1.0 - t)
            fb = ab * t + 0.0 * (1.0 - t)
            col  = imgui.get_color_u32_rgba(fr, fg, fb, aa)
            colb = imgui.get_color_u32_rgba(0, 0, 0, aa * 0.5)

            dl.add_triangle_filled(tip_x, tip_y, lx2, ly2, rx2, ry2, colb)
            dl.add_triangle_filled(tip_x, tip_y, lx2, ly2, rx2, ry2, col)

    # ── Sniper Cross ─────────────────────────────────────────────────────
    if menu_config.crosshair_sniper:
        cr, cg, cb, ca = menu_config.crosshair_sniper_color
        col  = imgui.get_color_u32_rgba(cr, cg, cb, ca)
        colb = imgui.get_color_u32_rgba(0, 0, 0, ca * 0.6)
        gap, size = 4, 12
        dl.add_line(cx-size, cy, cx-gap, cy, colb, 3.0)
        dl.add_line(cx+gap,  cy, cx+size, cy, colb, 3.0)
        dl.add_line(cx-size, cy, cx-gap, cy, col,  1.5)
        dl.add_line(cx+gap,  cy, cx+size, cy, col,  1.5)
        dl.add_line(cx, cy-size, cx, cy-gap, colb, 3.0)
        dl.add_line(cx, cy+gap,  cx, cy+size, colb, 3.0)
        dl.add_line(cx, cy-size, cx, cy-gap, col,  1.5)
        dl.add_line(cx, cy+gap,  cx, cy+size, col,  1.5)
        dl.add_circle_filled(cx, cy, 1.5, col)

    # ── Dynamic Cross (Nokta + Glow) ─────────────────────────────────────
    if menu_config.crosshair_dynamic:
        lp_addr = local.get("pawn")
        shots = pm.read_i32(lp_addr + off.iShotsFired) if lp_addr else 0
        speed = min(shots * 30.0, 250.0)

        # Dış glow boyutu
        base_s = menu_config.crosshair_dynamic_size * 0.3
        max_s  = menu_config.crosshair_dynamic_size
        target_size = base_s if speed < 10 else base_s + (max_s - base_s) * min(speed / 250.0, 1.0)
        _dyn_cross_size += (target_size - _dyn_cross_size) * 0.12
        s = max(1.0, _dyn_cross_size)

        # Merkez glow boyutu (bağımsız)
        cs = max(0.5, menu_config.crosshair_dynamic_core_size)

        gr, gg, gb, ga = menu_config.crosshair_dynamic_color
        wr, wg, wb, wa = menu_config.crosshair_dynamic_core

        # Dış radial glow — 6 katman, dıştan içe (halka yok)
        for i in range(6, 0, -1):
            gs     = s + i * s * 0.5
            glow_a = ga * (i / 6.0) * 0.55
            gcol   = imgui.get_color_u32_rgba(gr, gg, gb, glow_a)
            dl.add_circle_filled(cx, cy, gs, gcol, 48)

        # Merkez beyaz glow — 4 katman, bağımsız boyut
        for i in range(4, 0, -1):
            ws   = cs + i * cs * 0.6
            wa2  = wa * (i / 4.0) * 0.6
            wcol = imgui.get_color_u32_rgba(wr, wg, wb, wa2)
            dl.add_circle_filled(cx, cy, ws, wcol, 24)

        # Merkez nokta (tam opak)
        center = imgui.get_color_u32_rgba(wr, wg, wb, wa)
        dl.add_circle_filled(cx, cy, max(1.0, cs * 0.5), center, 16)

    # ── Recoil Cross ─────────────────────────────────────────────────────
    if menu_config.crosshair_recoil:
        lp_addr = local.get("pawn")
        if lp_addr:
            # Sol tık basılıyken ve punch anlamlıysa göster
            lmb = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
            if lmb:
                punch_raw = pm.read_memory(lp_addr + off.aimPunchAngle, 8)
                if punch_raw and len(punch_raw) >= 8:
                    pp, py2 = _f2(punch_raw, 0)
                    if abs(pp) > 0.1 or abs(py2) > 0.1:
                        if abs(pp) < 1000 and abs(py2) < 1000:
                            cr, cg, cb, ca = menu_config.crosshair_recoil_color
                            mult = (H / 90.0) * 1.5
                            rx = cx + (-py2 * mult)
                            ry = cy + ( pp  * mult)
                            col  = imgui.get_color_u32_rgba(cr, cg, cb, ca)
                            colb = imgui.get_color_u32_rgba(0, 0, 0, ca * 0.6)
                            L = 5
                            dl.add_line(rx-L, ry, rx+L, ry, colb, 3.0)
                            dl.add_line(rx, ry-L, rx, ry+L, colb, 3.0)
                            dl.add_line(rx-L, ry, rx+L, ry, col,  1.5)
                            dl.add_line(rx, ry-L, rx, ry+L, col,  1.5)
                            dl.add_circle_filled(rx, ry, 1.5, col)

while True:
    mk=bool(user32.GetAsyncKeyState(win32con.VK_INSERT)&0x8000)
    now=time.monotonic()
    if mk and not mk_last and now-mk_t>0.15:
        menu_open=not menu_open; mk_t=now
    mk_last=mk
    if menu_open!=menu_was:
        win32gui.SetWindowLong(hwnd,win32con.GWL_EXSTYLE,EX_MN if menu_open else EX_PT)
        menu_was=menu_open
    if menu_open:
        mx,my=win32api.GetCursorPos()
        io.mouse_pos=(float(mx),float(my))
        io.mouse_down[0]=bool(user32.GetAsyncKeyState(win32con.VK_LBUTTON)&0x8000)
        io.mouse_down[1]=bool(user32.GetAsyncKeyState(win32con.VK_RBUTTON)&0x8000)
    for ev in pygame.event.get():
        if menu_open: renderer.process_event(ev)

    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    imgui.new_frame()

    # ---- MENU ----
    if menu_open:
        imgui.begin("CS2Veil                    github@gkhantyln", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)
        imgui.begin_tab_bar("tabs")

        if imgui.begin_tab_item("Gorsel")[0]:
            _,menu_config.show_box_esp    =imgui.checkbox("Kutu ESP",        menu_config.show_box_esp)
            imgui.same_line()
            ch,v=imgui.color_edit4("Kutu Rengi##b",*menu_config.box_color,flags=imgui.COLOR_EDIT_NO_INPUTS)
            if ch: menu_config.box_color=list(v)
            _,menu_config.box_thickness   =imgui.slider_float("Kutu Kalinligi",menu_config.box_thickness,0.1,3.0,"%.2f")
            _,menu_config.box_width_scale =imgui.slider_float("Kutu Genisligi##bw",menu_config.box_width_scale,0.5,2.0,"%.2f")
            _,menu_config.box_height_scale=imgui.slider_float("Kutu Yuksekligi##bh",menu_config.box_height_scale,0.5,2.0,"%.2f")
            _,menu_config.show_bone_esp   =imgui.checkbox("Iskelet ESP",     menu_config.show_bone_esp)
            imgui.same_line()
            ch,v=imgui.color_edit4("Iskelet Rengi##sk",*menu_config.bone_color,flags=imgui.COLOR_EDIT_NO_INPUTS)
            if ch: menu_config.bone_color=list(v)
            _,menu_config.bone_thickness  =imgui.slider_float("Iskelet Kalinligi",menu_config.bone_thickness,0.1,2.0,"%.1f")
            _,menu_config.show_health_bar =imgui.checkbox("Can Bari",        menu_config.show_health_bar)
            _,menu_config.health_bar_type =imgui.combo("Can Bari Konumu",    menu_config.health_bar_type,["Sol","Ust","Sag","Alt"])
            _,menu_config.show_player_name=imgui.checkbox("Oyuncu Adi",      menu_config.show_player_name)
            if menu_config.show_player_name:
                imgui.same_line()
                ch,v=imgui.color_edit4("##namecolor",*menu_config.player_name_color,flags=imgui.COLOR_EDIT_NO_INPUTS|imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.player_name_color=list(v)
                _,menu_config.player_name_pos =imgui.combo("Konum##name",    menu_config.player_name_pos,["Ust","Alt"])
                _,menu_config.player_name_size=imgui.slider_int("Boyut##name",menu_config.player_name_size,8,24)
            _,menu_config.show_distance   =imgui.checkbox("Mesafe",          menu_config.show_distance)
            if menu_config.show_distance:
                imgui.same_line()
                ch,v=imgui.color_edit4("##distcolor",*menu_config.distance_color,flags=imgui.COLOR_EDIT_NO_INPUTS|imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.distance_color=list(v)
            _,menu_config.show_eye_ray    =imgui.checkbox("Bakis Cizgisi",   menu_config.show_eye_ray)
            imgui.same_line()
            ch,v=imgui.color_edit4("Bakis Rengi##er",*menu_config.eye_ray_color,flags=imgui.COLOR_EDIT_NO_INPUTS)
            if ch: menu_config.eye_ray_color=list(v)
            _,menu_config.show_line_to_enemy=imgui.checkbox("Dusmana Cizgi",menu_config.show_line_to_enemy)
            imgui.same_line()
            ch,v=imgui.color_edit4("Cizgi Rengi##le",*menu_config.line_to_enemy_color,flags=imgui.COLOR_EDIT_NO_INPUTS)
            if ch: menu_config.line_to_enemy_color=list(v)
            imgui.separator()
            _,menu_config.esp_fov_only=imgui.checkbox("Sadece FOV icindekiler (FPS+)",menu_config.esp_fov_only)
            imgui.separator()
            _,menu_config.show_dot_esp=imgui.checkbox("Nokta ESP##dot",menu_config.show_dot_esp)
            if menu_config.show_dot_esp:
                imgui.same_line()
                ch,v=imgui.color_edit4("##dotcol",*menu_config.dot_esp_color,flags=imgui.COLOR_EDIT_NO_INPUTS|imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.dot_esp_color=list(v)
                imgui.same_line()
                _,menu_config.dot_esp_size=imgui.slider_float("Boyut##dotsize",menu_config.dot_esp_size,1.0,10.0,"%.1f")
            imgui.end_tab_item()

        if imgui.begin_tab_item("Nishan Botu")[0]:
            _,aim_config.enabled=imgui.checkbox("Aktif##aim",aim_config.enabled)
            ch,aim_config.hotkey_index=imgui.combo("Tus##aim",aim_config.hotkey_index,AIM_HK)
            if ch: aim_config.apply_hotkey()
            _,aim_config.fov=imgui.slider_float("FOV",aim_config.fov,0.1,89.0,"%.1f")
            _,aim_config.show_fov_circle=imgui.checkbox("FOV Cemberi",aim_config.show_fov_circle)
            imgui.same_line()
            ch,v=imgui.color_edit4("FOV Rengi##fc",*aim_config.fov_color,flags=imgui.COLOR_EDIT_NO_INPUTS)
            if ch: aim_config.fov_color=list(v)
            _,aim_config.smooth=imgui.slider_float("Yumusatma",aim_config.smooth,0.0,0.9,"%.1f")
            _,aim_config.position=imgui.combo("Hedef (Normal)",aim_config.position,["Kafa","Boyun","Omuz","Gogus","Govde","Pelvis"])
            _,aim_config.position_pistol=imgui.combo("Hedef (Tabanca)",aim_config.position_pistol,["Kafa","Boyun","Omuz","Gogus","Govde","Pelvis"])
            _,aim_config.position_sniper=imgui.combo("Hedef (Keskin)",aim_config.position_sniper,["Kafa","Boyun","Omuz","Gogus","Govde","Pelvis"])
            _,aim_config.auto_shot=imgui.checkbox("Oto Ates",aim_config.auto_shot)
            imgui.same_line()
            _,aim_config.visible_check=imgui.checkbox("Gorunurluk",aim_config.visible_check)
            imgui.same_line()
            _,aim_config.target_lock=imgui.checkbox("Hedef Kilidi",aim_config.target_lock)
            _,aim_config.ignore_on_shot=imgui.checkbox("Ates Ederken Dur",aim_config.ignore_on_shot)
            imgui.same_line()
            _,aim_config.crouch_pred=imgui.checkbox("Cömelme Tahmini",aim_config.crouch_pred)
            imgui.separator()
            _,aim_config.shot_timing=imgui.checkbox("Aim Oturunca Ates Et",aim_config.shot_timing)
            if aim_config.shot_timing:
                _,aim_config.shot_threshold=imgui.slider_float("Ates Esigi##st",aim_config.shot_threshold,0.1,3.0,"%.2f")
                imgui.same_line(); imgui.text_colored("(dusuk=daha isabetli)",0.6,0.6,0.6,1)
            imgui.separator()
            _,aim_config.spray_control=imgui.checkbox("Spray Kontrol",aim_config.spray_control)
            imgui.same_line(); imgui.text_colored("(RCS ile birlikte acmayin - deneysel)",0.9,0.3,0.3,1)
            imgui.separator()
            # RCS - Recoil Control System
            imgui.text("--- Geri Tepme Kontrolu (RCS) ---")
            _,aim_config.rcs_enabled=imgui.checkbox("RCS Aktif",aim_config.rcs_enabled)
            if aim_config.rcs_enabled:
                _,aim_config.rcs_scale=imgui.slider_float("RCS Guc##rcs",aim_config.rcs_scale,0.1,2.0,"%.1f")
                imgui.text("  1.0 = tam kompanzasyon, 0.5 = yari")
            imgui.separator()
            _,aim_config.velocity_pred=imgui.checkbox("Hiz Tahmini",aim_config.velocity_pred)
            imgui.same_line(); imgui.text_colored("(Hareket eden hedefe one tahmin)",0.6,0.6,0.6,1)
            imgui.separator()
            imgui.text_colored(f"Aktif Tus: {AIM_HK[aim_config.hotkey_index]}",0.4,1,0.4,1)
            imgui.end_tab_item()

        if imgui.begin_tab_item("Tetik Botu")[0]:
            _,trigger_config.enabled=imgui.checkbox("Aktif##trig",trigger_config.enabled)
            ch,trigger_config.hotkey_index=imgui.combo("Tus##trig",trigger_config.hotkey_index,TRIG_HK)
            if ch: trigger_config.apply_hotkey()
            _,trigger_config.mode=imgui.combo("Mod",trigger_config.mode,["Tusa Basinca","Her Zaman"])
            _,trigger_config.delay_ms=imgui.slider_int("Gecikme(ms)",trigger_config.delay_ms,0,250)
            imgui.separator()
            imgui.text_colored(f"Aktif Tus: {TRIG_HK[trigger_config.hotkey_index]}",0.4,1,0.4,1)
            imgui.end_tab_item()

        if imgui.begin_tab_item("Ayarlar")[0]:
            _,menu_config.team_check=imgui.checkbox("Takim Kontrolu",menu_config.team_check)
            imgui.separator()
            _,menu_config.bhop_enabled=imgui.checkbox("Bunny Hop",menu_config.bhop_enabled)
            imgui.same_line(); imgui.text_colored("Space basili tutunca otomatik ziplama",0.6,0.6,0.6,1)
            imgui.separator()
            ch,menu_config.stream_proof=imgui.checkbox("Stream Proof (OBS Gizle)",menu_config.stream_proof)
            if ch:
                _apply_stream_proof(menu_config.stream_proof)
            imgui.same_line(); imgui.text_colored("OBS/Discord ekran paylasiminda gizler",0.6,0.6,0.6,1)
            imgui.separator()
            _,menu_config.no_flash=imgui.checkbox("No Flash",menu_config.no_flash)
            if not menu_config.no_flash:
                imgui.same_line()
                imgui.text("  Flash Seviyesi:")
                _,menu_config.flash_max_alpha=imgui.slider_int("##flash",menu_config.flash_max_alpha,0,255)
                imgui.text("  (255=hic flash, 0=tam flash)")
            imgui.separator()
            # Config kayit/yukle
            imgui.text("Config Yonetimi:")
            _cfg_files_cur = list_configs()
            changed, _cfg_name_buf[0] = imgui.input_text("Config Adi", _cfg_name_buf[0], 64)
            imgui.same_line()
            if imgui.button("Kaydet"):
                name = _cfg_name_buf[0].strip()
                if name:
                    if save_config(name, menu_config, aim_config, trigger_config, None):
                        _cfg_msg[0] = f"Kaydedildi: {name}.json"
                    else:
                        _cfg_msg[0] = "Kayit hatasi!"
                    _cfg_msg_time[0] = time.monotonic()
            for i, fname in enumerate(_cfg_files_cur):
                clicked, _ = imgui.selectable(fname, _cfg_selected[0] == i)
                if clicked: _cfg_selected[0] = i
            sel = _cfg_selected[0]
            has_sel = 0 <= sel < len(_cfg_files_cur)
            if imgui.button("Yukle") and has_sel:
                if load_config(_cfg_files_cur[sel], menu_config, aim_config, trigger_config, None):
                    _cfg_msg[0] = f"Yuklendi: {_cfg_files_cur[sel]}"
                else:
                    _cfg_msg[0] = "Yukleme hatasi!"
                _cfg_msg_time[0] = time.monotonic()
            imgui.same_line()
            if imgui.button("Sil") and has_sel:
                if delete_config(_cfg_files_cur[sel]):
                    _cfg_msg[0] = f"Silindi: {_cfg_files_cur[sel]}"
                    _cfg_selected[0] = -1
                _cfg_msg_time[0] = time.monotonic()
            if _cfg_msg[0] and time.monotonic() - _cfg_msg_time[0] < 2.0:
                imgui.text_colored(_cfg_msg[0], 0.4, 1.0, 0.4, 1.0)
            imgui.separator()
            imgui.text("INSERT = Menu ac/kapat")
            if imgui.button("Programi Kapat"): sys.exit(0)
            imgui.end_tab_item()

        if imgui.begin_tab_item("Crosshair")[0]:
            imgui.text("Nishangah Ayarlari")
            imgui.separator()

            # Recoil Cross
            _,menu_config.crosshair_recoil = imgui.checkbox("Recoil Cross##rc", menu_config.crosshair_recoil)
            if menu_config.crosshair_recoil:
                imgui.same_line()
                ch,v = imgui.color_edit4("##rcol", *menu_config.crosshair_recoil_color, flags=imgui.COLOR_EDIT_NO_INPUTS | imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.crosshair_recoil_color = list(v)
                imgui.same_line(); imgui.text_colored("Geri tepme gostergesi", 0.6,0.6,0.6,1)

            # Sniper Cross
            _,menu_config.crosshair_sniper = imgui.checkbox("Sniper Cross##sc", menu_config.crosshair_sniper)
            if menu_config.crosshair_sniper:
                imgui.same_line()
                ch,v = imgui.color_edit4("##scol", *menu_config.crosshair_sniper_color, flags=imgui.COLOR_EDIT_NO_INPUTS | imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.crosshair_sniper_color = list(v)
                imgui.same_line(); imgui.text_colored("Ince arti nishangah", 0.6,0.6,0.6,1)

            # Dynamic Cross
            _,menu_config.crosshair_dynamic = imgui.checkbox("Dynamic Cross##dc", menu_config.crosshair_dynamic)
            if menu_config.crosshair_dynamic:
                imgui.same_line()
                ch,v = imgui.color_edit4("Glow##dcol", *menu_config.crosshair_dynamic_color, flags=imgui.COLOR_EDIT_NO_INPUTS | imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.crosshair_dynamic_color = list(v)
                imgui.same_line()
                ch,v = imgui.color_edit4("Merkez##dcore", *menu_config.crosshair_dynamic_core, flags=imgui.COLOR_EDIT_NO_INPUTS | imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.crosshair_dynamic_core = list(v)
                imgui.same_line(); imgui.text_colored("Glow + Merkez (A = Opaklık)", 0.6,0.6,0.6,1)
                _,menu_config.crosshair_dynamic_size = imgui.slider_float(
                    "Dis Glow Boyutu##dynsize", menu_config.crosshair_dynamic_size, 1.0, 20.0, "%.1f")
                _,menu_config.crosshair_dynamic_core_size = imgui.slider_float(
                    "Merkez Boyutu##coresize", menu_config.crosshair_dynamic_core_size, 1.0, 10.0, "%.1f")

            # Snap Lines
            _,menu_config.crosshair_snaplines = imgui.checkbox("Snap Lines##sl", menu_config.crosshair_snaplines)
            if menu_config.crosshair_snaplines:
                imgui.same_line()
                ch,v = imgui.color_edit4("##slcol", *menu_config.crosshair_snaplines_color, flags=imgui.COLOR_EDIT_NO_INPUTS | imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.crosshair_snaplines_color = list(v)
                imgui.same_line(); imgui.text_colored("Renk (A = Opaklık)", 0.6,0.6,0.6,1)

            imgui.separator()

            # Dış Oklar
            _,menu_config.crosshair_arrows = imgui.checkbox("Dis Oklar##ar", menu_config.crosshair_arrows)
            if menu_config.crosshair_arrows:
                imgui.same_line()
                ch,v = imgui.color_edit4("##arcol", *menu_config.crosshair_arrows_color, flags=imgui.COLOR_EDIT_NO_INPUTS | imgui.COLOR_EDIT_ALPHA_PREVIEW)
                if ch: menu_config.crosshair_arrows_color = list(v)
                imgui.same_line(); imgui.text_colored("Baslangic rengi (HP'ye gore kirmiziya kayar)", 0.6,0.6,0.6,1)
                imgui.text_colored("  Renk secicide A = Opaklık", 0.5,0.5,0.5,1)

            imgui.end_tab_item()

        imgui.end_tab_bar()
        imgui.end()

    # ---- ESP ----
    dl=imgui.get_background_draw_list()
    with _lock: ents=list(_ents); local=_local

    if local:
        # Durum gostergesi
        if len(ents) > 0:
            dl.add_text(10, 10, imgui.get_color_u32_rgba(0, 1, 0, 1),
                        f"CS2Veil | {len(ents)}")
        else:
            dl.add_text(10, 10, imgui.get_color_u32_rgba(1, 0, 0, 1),
                        "CS2Veil")
        lt=local["team"]
        aim_pos=None; max_d=float('inf')

        for ent in ents[:64]:  # Max 64 entity render et — crash önleme
            team=ent["team"]; hp=ent["hp"]
            name=ent["name"]; bones=ent["bones"]; pos=ent["pos"]

            if menu_config.team_check and lt>=2 and team==lt: continue

            # quick_screen: head bone varsa ondan, yoksa entity loop'taki değerden
            head_scr = bones[BONEINDEX.head]["screen"] if len(bones) > BONEINDEX.head else None
            quick_screen = head_scr or ent.get("quick_screen")
            if not quick_screen: continue
            qx, qy = quick_screen
            if not(0 <= qx <= W and 0 <= qy <= H): continue

            # FOV filtresi
            if menu_config.esp_fov_only:
                cx_fov, cy_fov = W/2, H/2
                fov_r  = math.tan(aim_config.fov/180*math.pi/2)
                pawn_r = math.tan(max(local["fov"],1)/180*math.pi/2)
                fov_px = fov_r / pawn_r * W
                if math.sqrt((qx-cx_fov)**2 + (qy-cy_fov)**2) > fov_px:
                    continue

            # Ekrandaysa kemikleri kullan — screen entity loop'ta hesaplandı
            # (externalv2 mimarisi: render thread'de world_to_screen çağrısı yok)

            foot = ent.get("foot")
            if not foot:
                # foot yoksa head bone'dan hesapla
                foot = head_scr
            if not foot: continue
            fx,fy = foot

            head=bones[BONEINDEX.head]["screen"] if len(bones)>BONEINDEX.head and bones[BONEINDEX.head]["screen"] else None

            if not head: continue

            # Pelvis bone'u ayak olarak kullan (daha güvenilir)
            pelvis_scr = bones[0]["screen"] if len(bones) > 0 and bones[0]["screen"] else None
            foot_y = pelvis_scr[1] if pelvis_scr else fy

            if foot_y > head[1] + 5:
                bh = (foot_y - head[1]) * 1.15 * menu_config.box_height_scale
            else:
                bh = 80 * menu_config.box_height_scale
            bw = bh * 0.40 * menu_config.box_width_scale
            cx2 = head[0]
            # Üstten biraz boşluk bırak
            x1 = cx2 - bw/2
            y1 = head[1] - bh * 0.08
            x2 = cx2 + bw/2
            y2 = y1 + bh

            x1=max(x1,-10);y1=max(y1,-10);x2=min(x2,W+10);y2=min(y2,H+10)
            if x2-x1<3 or y2-y1<3: continue
            bh=max(y2-y1,10)

            if head:
                d=math.sqrt((head[0]-W/2)**2+(head[1]-H/2)**2)
                if d<max_d:
                    max_d=d
                    # Secili hitbox'a gore hedef bone
                    from core.bone import AIM_BONE_INDEX as _ABI2
                    _bone_map = _ABI2
                    _wpn = ent.get("weapon","")
                    if _wpn in PISTOLS:
                        _bidx = _bone_map[min(aim_config.position_pistol, len(_bone_map)-1)]
                    elif _wpn in SNIPERS:
                        _bidx = _bone_map[min(aim_config.position_sniper, len(_bone_map)-1)]
                    else:
                        _bidx = _bone_map[min(aim_config.position, len(_bone_map)-1)]
                    if len(bones) > _bidx and bones[_bidx]["pos"]:
                        ap = list(bones[_bidx]["pos"])
                        if _bidx == BONEINDEX.head:
                            ap[2] -= 1.0
                        # Hiz tahmini: hedefin hareketini 2.5 tick one tahmin et
                        if aim_config.velocity_pred:
                            vel = ent.get("vel", (0.0, 0.0, 0.0))
                            vx, vy, vz = vel
                            if (abs(vx) < 500 and abs(vy) < 500 and abs(vz) < 500
                                    and (abs(vx) + abs(vy) + abs(vz)) > 0.1):
                                pred_t = 0.015625 * 2.5  # ~2.5 tick
                                ap[0] += vx * pred_t
                                ap[1] += vy * pred_t
                                ap[2] += vz * pred_t
                        aim_pos = tuple(ap)

            if menu_config.show_box_esp:
                _bc = hp_color(hp, menu_config.box_color)
                _t  = menu_config.box_thickness
                # add_line kullan — add_rect'ten farklı olarak 0.1 gibi ince değerler gerçekten ince çıkar
                dl.add_line(x1, y1, x2, y1, _bc, _t)  # üst
                dl.add_line(x2, y1, x2, y2, _bc, _t)  # sağ
                dl.add_line(x2, y2, x1, y2, _bc, _t)  # alt
                dl.add_line(x1, y2, x1, y1, _bc, _t)  # sol

            if menu_config.show_dot_esp:
                # Gövde ortasına nokta — kutu merkezine
                dot_cx = (x1+x2)/2
                dot_cy = (y1+y2)/2
                dr,dg,db,da = menu_config.dot_esp_color
                dcol  = imgui.get_color_u32_rgba(dr,dg,db,da)
                dcolb = imgui.get_color_u32_rgba(0,0,0,da*0.6)
                ds = menu_config.dot_esp_size
                dl.add_circle_filled(dot_cx, dot_cy, ds+1, dcolb, 16)
                dl.add_circle_filled(dot_cx, dot_cy, ds,   dcol,  16)

            if menu_config.show_health_bar:
                bar_w = 3; bar_h = 3
                t = hp/100.0
                if t > 0.5: hcr,hcg = (1.0-t)*2, 1.0
                else:       hcr,hcg = 1.0, t*2
                bar_col = imgui.get_color_u32_rgba(hcr,hcg,0,0.9)
                bg_col  = imgui.get_color_u32_rgba(0.15,0.15,0.15,0.8)
                fr_col  = imgui.get_color_u32_rgba(0,0,0,0.5)
                box_w   = x2 - x1

                if menu_config.health_bar_type == 0:    # Sol - dikey
                    bx = x1 - bar_w - 2
                    dl.add_rect_filled(bx, y1, bx+bar_w, y2, bg_col, 1)
                    dl.add_rect_filled(bx, y2-bh*t, bx+bar_w, y2, bar_col, 1)
                    dl.add_rect(bx, y1, bx+bar_w, y2, fr_col, 1, 0, 0.5)

                elif menu_config.health_bar_type == 1:  # Ust - yatay (kutu genisligi)
                    by = y1 - bar_h - 2
                    dl.add_rect_filled(x1, by, x1+box_w, by+bar_h, bg_col, 1)
                    dl.add_rect_filled(x1, by, x1+box_w*t, by+bar_h, bar_col, 1)
                    dl.add_rect(x1, by, x1+box_w, by+bar_h, fr_col, 1, 0, 0.5)

                elif menu_config.health_bar_type == 2:  # Sag - dikey
                    bx = x2 + 2
                    dl.add_rect_filled(bx, y1, bx+bar_w, y2, bg_col, 1)
                    dl.add_rect_filled(bx, y2-bh*t, bx+bar_w, y2, bar_col, 1)
                    dl.add_rect(bx, y1, bx+bar_w, y2, fr_col, 1, 0, 0.5)

                elif menu_config.health_bar_type == 3:  # Alt - yatay (kutu genisligi)
                    by = y2 + 2
                    dl.add_rect_filled(x1, by, x1+box_w, by+bar_h, bg_col, 1)
                    dl.add_rect_filled(x1, by, x1+box_w*t, by+bar_h, bar_col, 1)
                    dl.add_rect(x1, by, x1+box_w, by+bar_h, fr_col, 1, 0, 0.5)

            if menu_config.show_bone_esp:
                bc = hp_color(hp, menu_config.bone_color, 0.9)
                for chain in BONE_CHAINS:
                    prev=None
                    for idx in chain:
                        if idx>=len(bones): continue
                        cur=bones[idx]
                        if prev and prev["screen"] and cur["screen"]:
                            ps,cs2=prev["screen"],cur["screen"]
                            if all(abs(v)<W*3 for v in [ps[0],ps[1],cs2[0],cs2[1]]):
                                dl.add_line(ps[0],ps[1],cs2[0],cs2[1],bc,menu_config.bone_thickness)
                        prev=cur

            if menu_config.show_eye_ray and len(bones)>BONEINDEX.head and bones[BONEINDEX.head]["screen"]:
                hb=bones[BONEINDEX.head]; ang=ent["ang"]
                p,y=ang[0]*math.pi/180,ang[1]*math.pi/180
                ll=math.cos(p)*50; hx,hy,hz=hb["pos"]
                end=ent.get("eye_end")
                if end and hb["screen"]:
                    dl.add_line(hb["screen"][0],hb["screen"][1],end[0],end[1],
                                imgui.get_color_u32_rgba(*menu_config.eye_ray_color),1.3)

            if menu_config.show_line_to_enemy:
                dl.add_line(fx,y1,W/2,0,imgui.get_color_u32_rgba(*menu_config.line_to_enemy_color),1.2)

            if menu_config.show_player_name:
                sz = menu_config.player_name_size
                # Kutu ortasina hizala (her karakter ~sz*0.5 px genislik)
                name_x = x1 + (x2 - x1) / 2 - len(name) * sz * 0.25
                if menu_config.player_name_pos == 0:  # Ust
                    name_y = y1 - sz - 2
                else:  # Alt
                    name_y = y2 + 2
                dl.add_text(name_x, name_y, imgui.get_color_u32_rgba(*menu_config.player_name_color), name)

            if menu_config.show_distance:
                lx,ly,lz=local["pos"]; ex2,ey,ez=pos
                dm=int(math.sqrt((ex2-lx)**2+(ey-ly)**2+(ez-lz)**2)/100)
                dl.add_text(x2+4,y1,imgui.get_color_u32_rgba(*menu_config.distance_color),f"{dm}m")

        if aim_config.show_fov_circle:
            fr=math.tan(aim_config.fov/180*math.pi/2)
            pr=math.tan(max(local["fov"],1)/180*math.pi/2)
            dl.add_circle(W/2,H/2,fr/pr*W,imgui.get_color_u32_rgba(*aim_config.fov_color),64,1.0)

        # Crosshair
        if any([menu_config.crosshair_recoil, menu_config.crosshair_sniper,
                menu_config.crosshair_dynamic, menu_config.crosshair_snaplines,
                menu_config.crosshair_arrows]):
            draw_crosshair(dl, local, ents)

        # Triggerbot - crosshair'daki dusmana ates et
        trig_key = bool(user32.GetAsyncKeyState(trigger_config.hotkey) & 0x8000)
        if trigger_config.enabled:
            if trigger_config.mode == 1 or (trigger_config.mode == 0 and trig_key):
                _triggerbot_check(local, ents)

    imgui.render()
    dd=imgui.get_draw_data()
    if dd.valid: renderer.render(dd)
    pygame.display.flip()
    clock.tick(60)  # Overlay icin 60fps yeterli
