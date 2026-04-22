"""
AimBot mod - mirrors C++ AimBot.hpp / AimControl namespace.
"""
import math
import win32con
from typing import Tuple

from core.entity import CEntity
from core.game import game
from utils.kmbox import kmbox

HOTKEY_LIST = [
    win32con.VK_LBUTTON,   # 0 - Sol Tık
    win32con.VK_LMENU,     # 1 - Sol ALT
    win32con.VK_RMENU,     # 2 - Sağ ALT
    win32con.VK_RBUTTON,   # 3 - Sağ Tık
    win32con.VK_XBUTTON1,  # 4 - Yan Tuş 1
    win32con.VK_XBUTTON2,  # 5 - Yan Tuş 2
    win32con.VK_CAPITAL,   # 6 - Caps Lock
    win32con.VK_LSHIFT,    # 7 - Sol Shift
    win32con.VK_LCONTROL,  # 8 - Sol Ctrl
]

HOTKEY_NAMES = [
    "Sol Tik",
    "Sol ALT",
    "Sag ALT",
    "Sag Tik",
    "Yan Tus 1",
    "Yan Tus 2",
    "Caps Lock",
    "Sol Shift",
    "Sol Ctrl",
]

PISTOLS  = {"hkp2000","glock","cz75a","deagle","elite","fiveseven","p250","revolver","tec9","usp_silencer"}
SNIPERS  = {"awp","g3sg1","scar20","ssg08"}
# RCS ve aim çalışmaması gereken silahlar (ateş edilemeyen ekipmanlar)
NO_RECOIL_WEAPONS = {
    "knife", "knife_t", "knife_ghost", "knife_gg",
    "c4",
    "hegrenade", "flashbang", "smokegrenade",
    "molotov", "incgrenade", "decoy",
    "tagrenade", "firebomb", "diversion", "frag_grenade", "snowball",
    "healthshot", "shield",
}


class AimConfig:
    def __init__(self):
        self.enabled        = True
        self.hotkey_index   = 1
        self.hotkey         = win32con.VK_LMENU
        self.fov            = 6.0
        self.smooth         = 0.3
        self.fake_smooth    = 0.8
        self.auto_shot      = False
        self.ignore_on_shot = True
        self.rcs_enabled    = False
        self.rcs_scale      = 1.0
        self.velocity_pred  = False
        self.visible_check  = True
        self.show_fov_circle= False
        self.fov_color      = [0.90, 0.90, 0.90, 1.0]
        self.position        = 1
        self.position_pistol = 0
        self.position_sniper = 2
        # ── Yeni özellikler ──────────────────────────────────────────────
        self.target_lock     = False   # Kilitlenen hedefe devam et
        self.shot_timing     = False   # Aim oturduğunda ateş et
        self.shot_threshold  = 0.8    # Ateş için gereken açı eşiği (derece)
        self.spray_control   = False   # Spray pattern kompansasyonu
        self.crouch_pred     = False   # Çömelme tahmini

    def apply_hotkey(self):
        if 0 <= self.hotkey_index < len(HOTKEY_LIST):
            self.hotkey = HOTKEY_LIST[self.hotkey_index]

    def get_bone_index(self, weapon: str):
        from core.bone import AIM_BONE_INDEX
        def _idx(pos): return AIM_BONE_INDEX[min(pos, len(AIM_BONE_INDEX)-1)]
        if weapon in PISTOLS:
            return _idx(self.position_pistol)
        if weapon in SNIPERS:
            return _idx(self.position_sniper)
        return _idx(self.position)


aim_config = AimConfig()

# ── CS2 Spray Pattern (ilk 30 mermi, pitch/yaw derece) ───────────────────────
# Kaynak: CS2 weapon recoil tabloları — pozitif pitch = yukarı kompanse
SPRAY_PATTERNS = {
    "ak47": [
        (0,0),(0.35,0.1),(0.9,0.15),(1.55,0.1),(2.25,-0.05),(2.9,-0.25),
        (3.4,-0.35),(3.65,-0.2),(3.6,0.1),(3.3,0.4),(2.85,0.55),(2.3,0.5),
        (1.75,0.3),(1.3,0.05),(1.0,-0.15),(0.85,-0.25),(0.85,-0.2),(1.0,-0.05),
        (1.2,0.1),(1.4,0.2),(1.5,0.2),(1.45,0.1),(1.3,-0.05),(1.05,-0.15),
        (0.75,-0.15),(0.45,-0.05),(0.2,0.1),(0.05,0.2),(0.0,0.2),(0.05,0.1),
    ],
    "m4a1": [
        (0,0),(0.25,0.05),(0.65,0.1),(1.1,0.05),(1.55,-0.05),(1.9,-0.2),
        (2.1,-0.3),(2.15,-0.2),(2.0,0.05),(1.75,0.3),(1.4,0.45),(1.0,0.4),
        (0.65,0.2),(0.4,0.0),(0.25,-0.15),(0.2,-0.2),(0.25,-0.15),(0.4,0.0),
        (0.6,0.15),(0.75,0.2),(0.8,0.15),(0.75,0.05),(0.6,-0.05),(0.4,-0.1),
        (0.2,-0.1),(0.05,0.0),(0.0,0.1),(0.05,0.15),(0.1,0.1),(0.1,0.05),
    ],
    "m4a1_silencer": [
        (0,0),(0.25,0.05),(0.65,0.1),(1.1,0.05),(1.55,-0.05),(1.9,-0.2),
        (2.1,-0.3),(2.15,-0.2),(2.0,0.05),(1.75,0.3),(1.4,0.45),(1.0,0.4),
        (0.65,0.2),(0.4,0.0),(0.25,-0.15),(0.2,-0.2),(0.25,-0.15),(0.4,0.0),
        (0.6,0.15),(0.75,0.2),(0.8,0.15),(0.75,0.05),(0.6,-0.05),(0.4,-0.1),
        (0.2,-0.1),(0.05,0.0),(0.0,0.1),(0.05,0.15),(0.1,0.1),(0.1,0.05),
    ],
    "famas": [
        (0,0),(0.3,0.1),(0.75,0.1),(1.2,0.0),(1.6,-0.15),(1.9,-0.3),
        (2.0,-0.3),(1.9,-0.1),(1.65,0.15),(1.3,0.35),(0.95,0.4),(0.6,0.3),
        (0.35,0.1),(0.2,-0.05),(0.15,-0.15),(0.2,-0.15),(0.35,-0.05),(0.55,0.1),
        (0.7,0.2),(0.75,0.2),(0.7,0.1),(0.55,0.0),(0.35,-0.1),(0.15,-0.1),
        (0.0,0.0),(0.0,0.1),(0.1,0.15),(0.15,0.1),(0.15,0.05),(0.1,0.0),
    ],
    "galil": [
        (0,0),(0.4,0.1),(1.0,0.15),(1.65,0.05),(2.25,-0.15),(2.7,-0.35),
        (2.95,-0.35),(2.9,-0.1),(2.55,0.25),(2.1,0.5),(1.6,0.55),(1.1,0.4),
        (0.7,0.15),(0.45,-0.05),(0.35,-0.2),(0.4,-0.25),(0.55,-0.15),(0.75,0.05),
        (0.95,0.2),(1.05,0.25),(1.05,0.15),(0.9,0.0),(0.65,-0.1),(0.4,-0.15),
        (0.15,-0.1),(0.0,0.0),(0.0,0.1),(0.1,0.15),(0.15,0.1),(0.1,0.0),
    ],
}
# Tanımsız silahlar için boş pattern
SPRAY_PATTERNS["default"] = [(0, 0)] * 30


def run_aimbot(local: CEntity, aim_pos: Tuple[float, float, float]):
    """Execute aimbot movement toward aim_pos."""
    if local.pawn.weapon_name == "knife":
        return
    from core.process_manager import process_mgr as pm
    if aim_config.ignore_on_shot and pm.is_key_down(win32con.VK_LBUTTON):
        return

    lx, ly, lz = local.pawn.camera_pos
    ax, ay, az = aim_pos

    dx = ax - lx
    dy = ay - ly
    dz = az - lz

    dist_2d = math.sqrt(dx * dx + dy * dy)
    yaw   = math.atan2(dy, dx) * 57.295779513 - local.pawn.view_angle[1]
    pitch = -math.atan2(dz, dist_2d) * 57.295779513 - local.pawn.view_angle[0]
    norm  = math.sqrt(yaw * yaw + pitch * pitch)

    if norm >= aim_config.fov:
        return

    screen = game.view.world_to_screen(aim_pos)
    if not screen:
        return

    sw, sh = game.view.screen_w, game.view.screen_h
    cx, cy = sw / 2, sh / 2
    sx, sy = screen

    fs = aim_config.fake_smooth if aim_config.fake_smooth != 0 else 1.5

    tx = (sx - cx) / fs if sx != cx else 0.0
    ty = (sy - cy) / fs if sy != cy else 0.0

    # Clamp
    if tx + cx > sw or tx + cx < 0:
        tx = 0.0
    if ty + cy > sh or ty + cy < 0:
        ty = 0.0

    dist_ratio   = norm / aim_config.fov
    speed_factor = 1.0 + (1.0 - dist_ratio)
    tx /= fs * speed_factor
    ty /= fs * speed_factor

    if aim_config.smooth > 0:
        kmbox.move_auto(tx, ty, 60 * aim_config.smooth)
    else:
        kmbox.move(tx, ty)

    if aim_config.auto_shot:
        from mods.triggerbot import run_triggerbot
        run_triggerbot(local)
