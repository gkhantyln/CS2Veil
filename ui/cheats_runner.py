"""
Cheats runner - entity okuma thread'de, cizim ana loop'ta.
"""
import math
import time
import struct
import threading
import win32con
import ctypes
import imgui

from core.game import game
from core.offsets import offsets as off
from core.process_manager import process_mgr as pm
from core.bone import BONEINDEX, BONE_JOINT_SIZE
from ui.menu import menu_config, render_menu
from ui.render import draw_health_bar
from mods.aimbot import aim_config
from mods.triggerbot import trigger_config
from utils.maps_data import map_state

_user32 = ctypes.WinDLL("user32")

# ---- Shared state ----
_menu_key_last = False
_menu_key_time = 0.0
_aim_key       = False
_trigger_key   = False

# Entity snapshot - thread tarafindan guncellenir
_entities_snapshot = []
_local_snapshot    = None
_snapshot_lock     = threading.Lock()


# ================================================================
# Background threads
# ================================================================

def _thread_matrix():
    while True:
        game.update_matrix()
        time.sleep(0.001)


def _thread_entity_list_entry():
    game.update_entity_list_entry()
    while True:
        time.sleep(5.0)
        game.update_entity_list_entry()


def _thread_read_entities():
    """Entity'leri arka planda oku, snapshot'i guncelle."""
    global _entities_snapshot, _local_snapshot
    while True:
        try:
            ents, local = _read_entities_impl()
            with _snapshot_lock:
                _entities_snapshot = ents
                _local_snapshot    = local
        except Exception:
            pass
        time.sleep(0.033)  # ~30 fps entity update


def start_background_threads():
    threading.Thread(target=_thread_matrix,            daemon=True).start()
    threading.Thread(target=_thread_entity_list_entry, daemon=True).start()
    threading.Thread(target=_thread_read_entities,     daemon=True).start()
    print("[ info ] Background threads started")


# ================================================================
# Entity okuma (thread'de calisir)
# ================================================================

def _read_entities_impl():
    ges        = pm.read_u64(game.address.entity_list)
    entry_base = game.address.entity_list_entry
    local_ctrl = pm.read_u64(game.address.local_controller)
    local_pawn = pm.read_u64(game.address.local_pawn)

    if not ges or not entry_base or not local_ctrl or not local_pawn:
        return [], None

    local_team = pm.read_i32(local_ctrl + off.TeamID)
    local_hp   = pm.read_i32(local_pawn  + off.CurrentHealth)
    local_pos  = pm.read_vec3(local_pawn + off.Pos)
    local_ang  = pm.read_vec2(local_pawn + off.angEyeAngles)
    local_cam  = pm.read_vec3(local_pawn + off.vecLastClipCameraPos)
    local_fov  = _read_fov(local_pawn)
    local_wpn  = _read_weapon_name(local_pawn)

    local_info = {
        "ctrl": local_ctrl, "pawn": local_pawn,
        "team": local_team, "hp": local_hp,
        "pos": local_pos, "ang": local_ang,
        "cam": local_cam, "fov": local_fov,
        "weapon": local_wpn, "ctrl_idx": 0,
    }

    entities = []
    for chunk_idx in range(4):
        chunk_ptr = pm.read_u64(entry_base + chunk_idx * 0x8)
        if not chunk_ptr or chunk_ptr > 0x7FFFFFFFFFFF or chunk_ptr < 0x10000:
            continue
        for ent_idx in range(512):
            ctrl = pm.read_u64(chunk_ptr + ent_idx * 0x8)
            if not ctrl or ctrl > 0x7FFFFFFFFFFF or ctrl < 0x10000:
                continue
            if ctrl == local_ctrl:
                local_info["ctrl_idx"] = chunk_idx * 512 + ent_idx
                continue

            if pm.read_i32(ctrl + off.IsAlive) != 1:
                continue

            name_raw = pm.read_memory(ctrl + off.iszPlayerName, 32)
            if not name_raw:
                continue
            end = name_raw.find(b'\x00')
            name = name_raw[:end].decode(errors="ignore") if end != -1 else ""
            if not name:
                continue

            team = pm.read_i32(ctrl + off.TeamID)

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

            pos  = pm.read_vec3(pawn + off.Pos)
            ang  = pm.read_vec2(pawn + off.angEyeAngles)
            wpn  = _read_weapon_name(pawn)
            bones = _read_bones(pawn)

            # Ayak screen - ankle bone veya pos
            foot = None
            if len(bones) > 24 and bones[24]["screen"]:
                foot = bones[24]["screen"]
            elif len(bones) > 27 and bones[27]["screen"]:
                foot = bones[27]["screen"]
            else:
                foot = game.view.world_to_screen(pos)

            entities.append({
                "ctrl": ctrl, "pawn": pawn,
                "name": name, "team": team,
                "hp": hp, "pos": pos, "ang": ang,
                "weapon": wpn, "bones": bones, "foot": foot,
            })

    return entities, local_info


def _read_weapon_name(pawn_addr: int) -> str:
    wpn = pm.trace_address(pawn_addr + off.pClippingWeapon, [0x10, 0x20, 0x0])
    if not wpn:
        return ""
    raw = pm.read_memory(wpn, 64)
    if not raw:
        return ""
    end = raw.find(b'\x00')
    name = raw[:end].decode(errors="ignore") if end != -1 else ""
    idx = name.find("_")
    return name[idx+1:] if idx != -1 else name


def _read_fov(pawn_addr: int) -> int:
    cam = pm.read_u64(pawn_addr + off.CameraServices)
    return pm.read_i32(cam + off.iFovStart) if cam else 90


def _read_bones(pawn_addr: int) -> list:
    scene = pm.read_u64(pawn_addr + off.GameSceneNode)
    if not scene:
        return []
    bone_arr = pm.read_u64(scene + off.BoneArray)
    if not bone_arr:
        return []
    raw = pm.read_memory(bone_arr, 30 * BONE_JOINT_SIZE)
    if not raw:
        return []
    bones = []
    for i in range(30):
        o = i * BONE_JOINT_SIZE
        if o + 12 > len(raw):
            break
        x, y, z = struct.unpack_from("<fff", raw, o)
        screen = game.view.world_to_screen((x, y, z))
        bones.append({"pos": (x, y, z), "screen": screen})
    return bones


# ================================================================
# Per-frame render (ana loop'ta calisir - hafif)
# ================================================================

def run_frame():
    global _menu_key_last, _menu_key_time, _aim_key, _trigger_key

    # INSERT toggle
    key_now = bool(_user32.GetAsyncKeyState(win32con.VK_INSERT) & 0x8000)
    now = time.monotonic()
    if key_now and not _menu_key_last and now - _menu_key_time > 0.15:
        menu_config.show_menu = not menu_config.show_menu
        _menu_key_time = now
    _menu_key_last = key_now

    _aim_key     = bool(_user32.GetAsyncKeyState(aim_config.hotkey)     & 0x8000)
    _trigger_key = bool(_user32.GetAsyncKeyState(trigger_config.hotkey) & 0x8000)

    if menu_config.show_menu:
        try:
            render_menu()
        except Exception as e:
            import traceback
            print(f"[ menu error ] {e}")
            traceback.print_exc()
            menu_config.show_menu = False

    # Snapshot al
    with _snapshot_lock:
        entities = list(_entities_snapshot)
        local    = _local_snapshot

    if not local:
        return

    draw_list  = imgui.get_background_draw_list()
    local_team = local["team"]
    sw, sh     = game.view.screen_w, game.view.screen_h
    aim_pos    = None
    max_dist   = float('inf')

    for ent in entities:
        team = ent["team"]
        foot = ent["foot"]
        hp   = ent["hp"]
        name = ent["name"]
        pos  = ent["pos"]
        bones= ent["bones"]

        # Takim filtresi
        if menu_config.team_check and local_team >= 2 and team == local_team:
            continue

        if foot is None:
            continue
        fx, fy = foot

        if not (-sw < fx < sw*2 and -sh < fy < sh*2):
            continue

        # Head bone
        head_screen = None
        if len(bones) > BONEINDEX.head and bones[BONEINDEX.head]["screen"]:
            head_screen = bones[BONEINDEX.head]["screen"]

        # Ankle bone (ayak) - en alt nokta
        ankle_screen = None
        for ankle_idx in [24, 27]:  # ankle_L, ankle_R
            if len(bones) > ankle_idx and bones[ankle_idx]["screen"]:
                ankle_screen = bones[ankle_idx]["screen"]
                break

        # Kutu: head'den ankle'a, genislik yuksekligin 0.4'u
        if head_screen and ankle_screen and ankle_screen[1] > head_screen[1]:
            hsx, hsy = head_screen
            asx, asy = ankle_screen
            box_h = asy - hsy
            box_w = box_h * 0.40
            cx = (hsx + asx) / 2
            x1, y1, x2, y2 = cx - box_w/2, hsy - box_h*0.05, cx + box_w/2, asy + box_h*0.05
        elif head_screen and head_screen[1] < fy:
            box_h = max(fy - head_screen[1], 10)
            box_w = box_h * 0.40
            cx = (fx + head_screen[0]) / 2
            x1, y1, x2, y2 = cx - box_w/2, head_screen[1], cx + box_w/2, fy
        else:
            x1, y1, x2, y2 = fx-18, fy-80, fx+18, fy

        # Kirp
        x1=max(x1,-10); y1=max(y1,-10)
        x2=min(x2,sw+10); y2=min(y2,sh+10)
        if x2-x1 < 3 or y2-y1 < 3:
            continue

        box_h = max(y2-y1, 10)

        # Aimbot hedef
        if head_screen:
            d = math.sqrt((head_screen[0]-sw/2)**2 + (head_screen[1]-sh/2)**2)
            if d < max_dist:
                max_dist = d
                if len(bones) > BONEINDEX.head:
                    ap = list(bones[BONEINDEX.head]["pos"])
                    ap[2] -= 1.0
                    aim_pos = tuple(ap)

        # ---- Cizim ----
        if menu_config.show_bone_esp:
            _draw_bones(bones, menu_config.bone_color, draw_list)

        if menu_config.show_eye_ray and len(bones) > BONEINDEX.head:
            _draw_eye_ray(bones[BONEINDEX.head], ent["ang"], draw_list)

        if menu_config.show_line_to_enemy:
            col = imgui.get_color_u32_rgba(*menu_config.line_to_enemy_color)
            draw_list.add_line(fx, y1, sw/2, 0, col, 1.2)

        if menu_config.show_box_esp:
            col = imgui.get_color_u32_rgba(*menu_config.box_color)
            draw_list.add_rect(x1, y1, x2, y2, col, 0, 0, 1.3)

        if menu_config.show_health_bar:
            if menu_config.health_bar_type == 0:
                draw_health_bar(ent["pawn"], 100, hp, (x1-7, y1), (7, box_h), False, draw_list)
            else:
                draw_health_bar(ent["pawn"], 100, hp, (fx-35, y1-13), (70, 8), True, draw_list)

        if menu_config.show_weapon_esp and ent["weapon"]:
            draw_list.add_text(x1, y2+2, imgui.get_color_u32_rgba(1,1,1,1), ent["weapon"])

        if menu_config.show_player_name:
            ny = y1 - 14
            draw_list.add_text(x1, ny, imgui.get_color_u32_rgba(1,1,1,1), name)

        if menu_config.show_distance:
            lx,ly,lz = local["pos"]
            ex,ey,ez = pos
            dm = int(math.sqrt((ex-lx)**2+(ey-ly)**2+(ez-lz)**2)/100)
            draw_list.add_text(x2+4, y1, imgui.get_color_u32_rgba(1,1,1,1), f"{dm}m")

    # FOV cemberi
    if aim_config.show_fov_circle:
        fov_r  = math.tan(aim_config.fov/180*math.pi/2)
        pawn_r = math.tan(max(local["fov"],1)/180*math.pi/2)
        radius = fov_r / pawn_r * sw
        col = imgui.get_color_u32_rgba(*aim_config.fov_color)
        draw_list.add_circle(sw/2, sh/2, radius, col, 64, 1.0)

    # Triggerbot
    if trigger_config.enabled:
        if trigger_config.mode == 1 or (trigger_config.mode == 0 and _trigger_key):
            pass  # TODO

    # Aimbot
    if aim_config.enabled and _aim_key and aim_pos:
        _run_aimbot(local, aim_pos)


def _draw_bones(bones, color, draw_list):
    from core.bone import BONE_CHAINS
    col = imgui.get_color_u32_rgba(*color)
    sw, sh = game.view.screen_w, game.view.screen_h
    for chain in BONE_CHAINS:
        prev = None
        for idx in chain:
            if idx >= len(bones): continue
            cur = bones[idx]
            if prev and prev["screen"] and cur["screen"]:
                px, py = prev["screen"]
                cx, cy = cur["screen"]
                # Gecersiz koordinatlari atla
                if (abs(px) > sw*3 or abs(py) > sh*3 or
                    abs(cx) > sw*3 or abs(cy) > sh*3):
                    prev = cur
                    continue
                draw_list.add_line(px, py, cx, cy, col, 1.3)
            prev = cur


def _draw_eye_ray(head_bone, view_angle, draw_list):
    if not head_bone["screen"]: return
    p, y = view_angle[0]*math.pi/180, view_angle[1]*math.pi/180
    ll = math.cos(p) * 50
    hx,hy,hz = head_bone["pos"]
    end = game.view.world_to_screen((hx+math.cos(y)*ll, hy+math.sin(y)*ll, hz-math.sin(p)*50))
    if end:
        sx,sy = head_bone["screen"]
        col = imgui.get_color_u32_rgba(*menu_config.eye_ray_color)
        draw_list.add_line(sx, sy, end[0], end[1], col, 1.3)


def _run_aimbot(local, aim_pos):
    from utils.kmbox import kmbox
    if local["weapon"] == "knife": return
    if aim_config.ignore_on_shot and bool(_user32.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000): return

    lx,ly,lz = local["cam"]
    ax,ay,az = aim_pos
    dx,dy,dz = ax-lx, ay-ly, az-lz
    d2 = math.sqrt(dx*dx+dy*dy)
    yaw   = math.atan2(dy,dx)*57.295779513 - local["ang"][1]
    pitch = -math.atan2(dz,d2)*57.295779513 - local["ang"][0]
    norm  = math.sqrt(yaw*yaw+pitch*pitch)
    if norm >= aim_config.fov: return

    screen = game.view.world_to_screen(aim_pos)
    if not screen: return
    sw,sh = game.view.screen_w, game.view.screen_h
    cx,cy = sw/2, sh/2
    sx,sy = screen
    fs = aim_config.fake_smooth or 1.5
    tx = (sx-cx)/fs if sx!=cx else 0.0
    ty = (sy-cy)/fs if sy!=cy else 0.0
    if tx+cx>sw or tx+cx<0: tx=0.0
    if ty+cy>sh or ty+cy<0: ty=0.0
    sf = 1.0+(1.0-norm/aim_config.fov)
    tx/=fs*sf; ty/=fs*sf
    if aim_config.smooth>0: kmbox.move_auto(tx,ty,60*aim_config.smooth)
    else: kmbox.move(tx,ty)
