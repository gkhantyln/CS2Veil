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
from mods.aimbot import aim_config, HOTKEY_NAMES as AIM_HK, PISTOLS, SNIPERS
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

def _read_bones(pawn):
    sc=pm.read_u64(pawn+off.GameSceneNode)
    if not sc: return []
    ba=pm.read_u64(sc+off.BoneArray)
    if not ba: return []
    r=pm.read_memory(ba, 28 * BONE_JOINT_SIZE)
    if not r: return []
    out=[]
    for i in range(28):
        o=i*BONE_JOINT_SIZE
        if o+12>len(r): break
        x,y,z=_f3(r,o)
        out.append({"pos":(x,y,z),"screen":None})
    return out

def _entity_loop():
    global _ents,_local
    last_entry_update = 0
    last_weapon_update = 0
    _weapon_cache = {}  # pawn_addr -> weapon_name cache
    while True:
        try:
            # Matrix her iterasyonda guncelle (entity thread'de)
            game.update_matrix()
            now = time.monotonic()

            # Entity list entry her saniye guncelle
            if now - last_entry_update > 1.0:
                game.update_entity_list_entry()
                last_entry_update = now
            ges=pm.read_u64(game.address.entity_list)
            base=game.address.entity_list_entry
            lc=pm.read_u64(game.address.local_controller)
            lp=pm.read_u64(game.address.local_pawn)
            if not all([ges,base,lc,lp]):
                # entry_list_entry 0 ise hemen guncelle
                if not base:
                    game.update_entity_list_entry()
                    last_entry_update = time.monotonic()
                time.sleep(0.05); continue
            cs=pm.read_u64(lp+off.CameraServices)
            # Local player: tek batch okuma
            lp_buf = pm.read_pawn_block(lp)
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
                cs=pm.read_u64(lp+off.CameraServices)
                loc={"ctrl":lc,"pawn":lp,
                     "team":pm.read_i32(lc+off.TeamID),
                     "hp":pm.read_i32(lp+off.CurrentHealth),
                     "pos":pm.read_vec3(lp+off.Pos),
                     "ang":pm.read_vec2(lp+off.angEyeAngles),
                     "cam":pm.read_vec3(lp+off.vecLastClipCameraPos),
                     "fov":pm.read_i32(cs+off.iFovStart) if cs else 90,
                     "weapon":_read_weapon(lp),"idx":0}
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

                    # Weapon name: cache ile seyrek oku (500ms)
                    wpn = _weapon_cache.get(pawn, "")
                    if now - last_weapon_update > 0.5:
                        wpn = _read_weapon(pawn)
                        _weapon_cache[pawn] = wpn

                    # Bones: GameSceneNode pawn_buf'tan, BoneArray ayrı okuma
                    sc = _u64(pawn_buf, off.GameSceneNode)
                    bones = []
                    if sc and sc < 0x7FFFFFFFFFFF:
                        ba = pm.read_u64(sc + off.BoneArray)
                        if ba:
                            r = pm.read_memory(ba, 28 * BONE_JOINT_SIZE)
                            if r:
                                for bi in range(28):
                                    o = bi * BONE_JOINT_SIZE
                                    if o+12 > len(r): break
                                    bones.append({"pos": _f3(r, o), "screen": None})

                    foot = game.view.world_to_screen(pos)
                    tmp.append({"ctrl":ctrl,"pawn":pawn,"name":name,"team":team,"hp":hp,
                                "pos":pos,"ang":ang,"vel":vel,"weapon":wpn,"bones":bones,"foot":foot})
            with _lock: _ents=tmp; _local=loc

            # ── Aimbot (333Hz) ───────────────────────────────────────────────
            if aim_config.enabled and loc:
                _ak = bool(user32.GetAsyncKeyState(aim_config.hotkey) & 0x8000)
                if _ak:
                    _aim_pos = None
                    _max_d   = float('inf')
                    _lt      = loc["team"]
                    for _ent in tmp:
                        if menu_config.team_check and _lt >= 2 and _ent["team"] == _lt:
                            continue
                        _bones = _ent["bones"]
                        if len(_bones) <= BONEINDEX.head or not _bones[BONEINDEX.head]["pos"]:
                            continue
                        # Ekran mesafesi yerine kamera açı mesafesi kullan
                        _lx,_ly,_lz = loc["cam"]
                        _bx,_by,_bz = _bones[BONEINDEX.head]["pos"]
                        _dx,_dy = _bx-_lx, _by-_ly
                        _d2 = math.sqrt(_dx*_dx+_dy*_dy)
                        if _d2 < 0.001: continue
                        _ty = math.atan2(_dy,_dx)*57.295779513
                        _tp = -math.atan2(_bz-_lz,_d2)*57.295779513
                        _cp,_cy2 = loc["ang"]
                        _dyw = _ty - _cy2
                        while _dyw >  180: _dyw -= 360
                        while _dyw < -180: _dyw += 360
                        _dpt = _tp - _cp
                        _dist = math.sqrt(_dyw**2+_dpt**2)
                        if _dist < _max_d and _dist < aim_config.fov:
                            _max_d = _dist
                            _bone_map = [BONEINDEX.head, BONEINDEX.neck_0, BONEINDEX.spine_1]
                            _wpn = _ent.get("weapon","")
                            if _wpn in PISTOLS:
                                _bidx = _bone_map[min(aim_config.position_pistol,2)]
                            elif _wpn in SNIPERS:
                                _bidx = _bone_map[min(aim_config.position_sniper,2)]
                            else:
                                _bidx = _bone_map[min(aim_config.position,2)]
                            if len(_bones) > _bidx:
                                _ap = list(_bones[_bidx]["pos"])
                                if _bidx == BONEINDEX.head: _ap[2] -= 1.0
                                if aim_config.velocity_pred:
                                    _vx,_vy,_vz = _ent.get("vel",(0,0,0))
                                    if abs(_vx)<500 and abs(_vy)<500 and (abs(_vx)+abs(_vy))>0.1:
                                        _pt = 0.015625*2.5
                                        _ap[0]+=_vx*_pt; _ap[1]+=_vy*_pt; _ap[2]+=_vz*_pt
                                _aim_pos = tuple(_ap)

                    if _aim_pos:
                        _ax,_ay,_az = _aim_pos
                        _lx,_ly,_lz = loc["cam"]
                        _dx,_dy,_dz = _ax-_lx,_ay-_ly,_az-_lz
                        _d2 = math.sqrt(_dx*_dx+_dy*_dy)
                        if _d2 > 0.001:
                            _tyw = math.atan2(_dy,_dx)*57.295779513
                            _tpt = -math.atan2(_dz,_d2)*57.295779513
                            _pp,_py2 = loc.get("punch",(0.0,0.0))
                            _tpt -= _pp*2.0; _tyw -= _py2*2.0
                            _cp,_cy2 = loc["ang"]
                            _dyw = _tyw-_cy2
                            while _dyw >  180: _dyw -= 360
                            while _dyw < -180: _dyw += 360
                            _dpt = _tpt-_cp
                            _norm = math.sqrt(_dyw**2+_dpt**2)
                            if _norm < aim_config.fov:
                                _sm = max(aim_config.smooth, 0.05)
                                _nyw = _cy2 + _dyw*(1.0-_sm)
                                _npt = _cp  + _dpt*(1.0-_sm)
                                _npt = max(-89.0,min(89.0,_npt))
                                pm.write_memory(game.address.view_angle,
                                                struct.pack("<ff",_npt,_nyw))
                                if aim_config.auto_shot:
                                    _triggerbot_shoot()

            # ── RCS (333Hz) ──────────────────────────────────────────────────
            if aim_config.rcs_enabled and loc:
                _lp = loc["pawn"]
                if _lp:
                    # Sadece sol tık basılıyken çalış
                    if user32.GetAsyncKeyState(0x01) & 0x8000:
                        _shots_r = pm.read_memory(_lp + off.iShotsFired, 4)
                        _shots   = _u32(_shots_r, 0) if _shots_r else 0
                        if _shots > 1:
                            _pp,_py2 = loc.get("punch",(0.0,0.0))
                            # Punch sıfırsa RCS uygulama
                            if abs(_pp) > 0.01 or abs(_py2) > 0.01:
                                _ca = pm.read_vec2(_lp + off.angEyeAngles)
                                _np = max(-89.0,min(89.0,_ca[0]-_pp*aim_config.rcs_scale))
                                _ny = _ca[1]-_py2*aim_config.rcs_scale
                                game.set_view_angle(_np,_ny)
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
        time.sleep(0.003)  # ~333fps entity update

threading.Thread(target=_entity_loop,daemon=True).start()

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
            _,menu_config.box_type        =imgui.combo("Kutu Tipi",          menu_config.box_type,["Normal","Ince"])
            _,menu_config.show_bone_esp   =imgui.checkbox("Iskelet ESP",     menu_config.show_bone_esp)
            imgui.same_line()
            ch,v=imgui.color_edit4("Iskelet Rengi##sk",*menu_config.bone_color,flags=imgui.COLOR_EDIT_NO_INPUTS)
            if ch: menu_config.bone_color=list(v)
            _,menu_config.show_health_bar =imgui.checkbox("Can Bari",        menu_config.show_health_bar)
            _,menu_config.health_bar_type =imgui.combo("Can Bari Konumu",    menu_config.health_bar_type,["Sol","Ust","Sag","Alt"])
            _,menu_config.show_player_name=imgui.checkbox("Oyuncu Adi",      menu_config.show_player_name)
            if menu_config.show_player_name:
                _,menu_config.player_name_pos =imgui.combo("Konum##name",    menu_config.player_name_pos,["Ust","Alt"])
                _,menu_config.player_name_size=imgui.slider_int("Boyut##name",menu_config.player_name_size,8,24)
            _,menu_config.show_distance   =imgui.checkbox("Mesafe",          menu_config.show_distance)
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
            _,aim_config.position=imgui.combo("Hedef (Normal)",aim_config.position,["Kafa","Boyun","Govde"])
            _,aim_config.position_pistol=imgui.combo("Hedef (Tabanca)",aim_config.position_pistol,["Kafa","Boyun","Govde"])
            _,aim_config.position_sniper=imgui.combo("Hedef (Keskin)",aim_config.position_sniper,["Kafa","Boyun","Govde"])
            _,aim_config.auto_shot=imgui.checkbox("Oto Ates",aim_config.auto_shot)
            imgui.same_line()
            _,aim_config.visible_check=imgui.checkbox("Gorunurluk",aim_config.visible_check)
            _,aim_config.ignore_on_shot=imgui.checkbox("Ates Ederken Dur",aim_config.ignore_on_shot)
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
                        f"CS2Veil  |  Aktif  |  Entity: {len(ents)}")
        else:
            dl.add_text(10, 10, imgui.get_color_u32_rgba(1, 0, 0, 1),
                        "CS2Veil  |  Deaktif")
        lt=local["team"]
        aim_pos=None; max_d=float('inf')

        for ent in ents:
            team=ent["team"]; hp=ent["hp"]
            name=ent["name"]; bones=ent["bones"]; pos=ent["pos"]

            if menu_config.team_check and lt>=2 and team==lt: continue

            # Once sadece pos ile on eleme - ekranda mi?
            quick_screen = game.view.world_to_screen(pos)
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

            # Ekrandaysa kemikleri hesapla (sadece gorunenler icin)
            for b in bones:
                b["screen"] = game.view.world_to_screen(b["pos"])

            foot = None
            for ai in [24,27]:
                if len(bones)>ai and bones[ai]["screen"]: foot=bones[ai]["screen"]; break
            if not foot: foot=game.view.world_to_screen(pos)
            if not foot: continue
            fx,fy = foot

            head=bones[BONEINDEX.head]["screen"] if len(bones)>BONEINDEX.head and bones[BONEINDEX.head]["screen"] else None
            ankle=None
            for ai in [24,27]:
                if len(bones)>ai and bones[ai]["screen"]: ankle=bones[ai]["screen"]; break

            if not(-W<fx<W*2 and -H<fy<H*2): continue

            if head and ankle and ankle[1]>head[1]:
                bh=ankle[1]-head[1]; bw=bh*0.40; cx2=(head[0]+ankle[0])/2
                x1,y1,x2,y2=cx2-bw/2,head[1]-bh*0.05,cx2+bw/2,ankle[1]+bh*0.05
            elif head and head[1]<fy:
                bh=max(fy-head[1],10); cx2=(fx+head[0])/2
                x1,y1,x2,y2=cx2-bh*0.20,head[1],cx2+bh*0.20,fy
            else:
                x1,y1,x2,y2=fx-18,fy-80,fx+18,fy

            x1=max(x1,-10);y1=max(y1,-10);x2=min(x2,W+10);y2=min(y2,H+10)
            if x2-x1<3 or y2-y1<3: continue
            bh=max(y2-y1,10)

            if head:
                d=math.sqrt((head[0]-W/2)**2+(head[1]-H/2)**2)
                if d<max_d:
                    max_d=d
                    # Secili hitbox'a gore hedef bone
                    _bone_map = [BONEINDEX.head, BONEINDEX.neck_0, BONEINDEX.spine_1]
                    _wpn = ent.get("weapon","")
                    if _wpn in PISTOLS:
                        _bidx = _bone_map[min(aim_config.position_pistol, 2)]
                    elif _wpn in SNIPERS:
                        _bidx = _bone_map[min(aim_config.position_sniper, 2)]
                    else:
                        _bidx = _bone_map[min(aim_config.position, 2)]
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
                dl.add_rect(x1,y1,x2,y2, hp_color(hp, menu_config.box_color), 0, 0, 1.5)

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
                                dl.add_line(ps[0],ps[1],cs2[0],cs2[1],bc,1.5)
                        prev=cur

            if menu_config.show_eye_ray and len(bones)>BONEINDEX.head and bones[BONEINDEX.head]["screen"]:
                hb=bones[BONEINDEX.head]; ang=ent["ang"]
                p,y=ang[0]*math.pi/180,ang[1]*math.pi/180
                ll=math.cos(p)*50; hx,hy,hz=hb["pos"]
                end=game.view.world_to_screen((hx+math.cos(y)*ll,hy+math.sin(y)*ll,hz-math.sin(p)*50))
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
                dl.add_text(name_x, name_y, imgui.get_color_u32_rgba(1,1,1,1), name)

            if menu_config.show_distance:
                lx,ly,lz=local["pos"]; ex2,ey,ez=pos
                dm=int(math.sqrt((ex2-lx)**2+(ey-ly)**2+(ez-lz)**2)/100)
                dl.add_text(x2+4,y1,imgui.get_color_u32_rgba(1,1,1,1),f"{dm}m")

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
