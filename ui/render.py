"""
ESP render helpers - flat coordinate draw_list API (pyimgui 2.x).
"""
import math
import time
import imgui
from typing import Dict, Tuple, Optional

from core.entity import CEntity
from core.bone import BONE_CHAINS, BONEINDEX
from core.game import game
from mods.aimbot import aim_config


def _col(r, g, b, a=1.0):
    return imgui.get_color_u32_rgba(r, g, b, a)

def _list_col(c):
    return imgui.get_color_u32_rgba(c[0], c[1], c[2], c[3])


def draw_fov_circle(local: CEntity, draw_list):
    if not aim_config.show_fov_circle:
        return
    sw, sh = game.view.screen_w, game.view.screen_h
    cx, cy = sw / 2, sh / 2
    fov_rad  = math.tan(aim_config.fov / 180.0 * math.pi / 2.0)
    pawn_fov = local.pawn.fov if local.pawn.fov > 0 else 90
    pawn_rad = math.tan(pawn_fov / 180.0 * math.pi / 2.0)
    radius   = fov_rad / pawn_rad * sw
    c = aim_config.fov_color
    draw_list.add_circle(cx, cy, radius, _list_col(c), 64, 1.0)


def draw_bone(entity: CEntity, color, thickness: float, draw_list):
    bone = entity.get_bone()
    if not bone.bone_list:
        return
    col = _list_col(color)
    for chain in BONE_CHAINS:
        prev = None
        for idx in chain:
            if idx >= len(bone.bone_list):
                continue
            cur = bone.bone_list[idx]
            if prev and prev.is_visible and cur.is_visible and prev.screen_pos and cur.screen_pos:
                draw_list.add_line(
                    prev.screen_pos[0], prev.screen_pos[1],
                    cur.screen_pos[0],  cur.screen_pos[1],
                    col, thickness
                )
            prev = cur


def draw_eye_ray(entity: CEntity, length: float, color, thickness: float, draw_list):
    bone = entity.get_bone()
    if not bone.bone_list or BONEINDEX.head >= len(bone.bone_list):
        return
    head = bone.bone_list[BONEINDEX.head]
    if not head.is_visible or not head.screen_pos:
        return
    pitch_r = entity.pawn.view_angle[0] * math.pi / 180
    yaw_r   = entity.pawn.view_angle[1] * math.pi / 180
    line_len = math.cos(pitch_r) * length
    hx, hy, hz = head.pos
    ex = hx + math.cos(yaw_r) * line_len
    ey = hy + math.sin(yaw_r) * line_len
    ez = hz - math.sin(pitch_r) * length
    end_screen = game.view.world_to_screen((ex, ey, ez))
    if end_screen:
        draw_list.add_line(
            head.screen_pos[0], head.screen_pos[1],
            end_screen[0], end_screen[1],
            _list_col(color), thickness
        )


def get_2d_box(entity: CEntity) -> Optional[Tuple[float, float, float, float]]:
    bone = entity.get_bone()
    if not bone.bone_list or BONEINDEX.head >= len(bone.bone_list):
        return None
    head = bone.bone_list[BONEINDEX.head]
    foot = entity.pawn.screen_pos
    if not head.screen_pos or not foot:
        return None
    h = (foot[1] - head.screen_pos[1]) * 1.09
    w = h * 0.6
    x = foot[0] - w / 2
    y = head.screen_pos[1] - h * 0.08
    return (x, y, w, h)


def get_2d_bone_box(entity: CEntity) -> Optional[Tuple[float, float, float, float]]:
    bone = entity.get_bone()
    if not bone.bone_list:
        return None
    visible = [b for b in bone.bone_list if b.is_visible and b.screen_pos]
    if not visible:
        return None
    xs = [b.screen_pos[0] for b in visible]
    ys = [b.screen_pos[1] for b in visible]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return (min_x, min_y, max_x - min_x, max_y - min_y)


def draw_line_to_enemy(rect: Tuple, color, thickness: float, draw_list):
    x, y, w, h = rect
    cx = game.view.screen_w / 2
    draw_list.add_line(x + w / 2, y, cx, 0, _list_col(color), thickness)


def draw_distance(local: CEntity, entity: CEntity, rect: Tuple, draw_list):
    lx, ly, lz = local.pawn.pos
    ex, ey, ez = entity.pawn.pos
    dist = int(math.sqrt((ex-lx)**2 + (ey-ly)**2 + (ez-lz)**2) / 100)
    x, y, w, h = rect
    draw_list.add_text(x + w + 4, y, _col(1, 1, 1), f"{dist}m")


class HealthBarState:
    SHOW_BACKUP_DURATION = 0.5

    def __init__(self):
        self.last_backup_hp: float = 0.0
        self.in_show_backup: bool  = False
        self.backup_start:   float = 0.0

    def _mix(self, c1, c2, t):
        return tuple(t * a + (1 - t) * b for a, b in zip(c1, c2))

    def _hp_color(self, proportion: float):
        first  = (0.376, 0.965, 0.443, 0.863)
        second = (0.969, 0.839, 0.404, 0.863)
        third  = (1.0,   0.373, 0.373, 0.863)
        t = proportion ** 2.5
        if proportion > 0.5:
            return self._mix(first, second, t * 3 - 1)
        return self._mix(second, third, t * 4)

    def draw_vertical(self, max_hp: float, hp: float,
                      pos: Tuple, size: Tuple, draw_list):
        x, y   = pos
        w, h   = size
        proportion = hp / max_hp if max_hp > 0 else 0
        bar_h  = h * proportion
        bg_col    = _col(0.353, 0.353, 0.353, 0.863)
        frame_col = _col(0.176, 0.176, 0.176, 0.863)

        draw_list.add_rect_filled(x, y, x + w, y + h, bg_col, 5)

        now = time.monotonic()
        if self.last_backup_hp == 0 or self.last_backup_hp < hp:
            self.last_backup_hp = hp
        if self.last_backup_hp != hp:
            if not self.in_show_backup:
                self.backup_start   = now
                self.in_show_backup = True
            elapsed = now - self.backup_start
            if elapsed > self.SHOW_BACKUP_DURATION:
                self.last_backup_hp = hp
                self.in_show_backup = False
            elif self.in_show_backup:
                backup_h = self.last_backup_hp / max_hp * h
                alpha    = 1 - 0.95 * (elapsed / self.SHOW_BACKUP_DURATION)
                lerp     = elapsed / self.SHOW_BACKUP_DURATION * (backup_h - bar_h)
                backup_h -= lerp
                draw_list.add_rect_filled(
                    x, y + h - backup_h, x + w, y + h,
                    _col(1, 1, 1, alpha), 5
                )

        col = self._hp_color(proportion)
        draw_list.add_rect_filled(x, y + h - bar_h, x + w, y + h,
                                   imgui.get_color_u32_rgba(*col), 5)
        draw_list.add_rect(x, y, x + w, y + h, frame_col, 5, 0, 1)

    def draw_horizontal(self, max_hp: float, hp: float,
                        pos: Tuple, size: Tuple, draw_list):
        x, y  = pos
        w, h  = size
        proportion = hp / max_hp if max_hp > 0 else 0
        bar_w = w * proportion
        bg_col    = _col(0.353, 0.353, 0.353, 0.863)
        frame_col = _col(0.176, 0.176, 0.176, 0.863)
        draw_list.add_rect_filled(x, y, x + w, y + h, bg_col, 5)
        col = self._hp_color(proportion)
        draw_list.add_rect_filled(x, y, x + bar_w, y + h,
                                   imgui.get_color_u32_rgba(*col), 5)
        draw_list.add_rect(x, y, x + w, y + h, frame_col, 5, 0, 1)


_health_bar_map: Dict[int, HealthBarState] = {}


def draw_health_bar(sign: int, max_hp: float, hp: float,
                    pos: Tuple, size: Tuple, horizontal: bool, draw_list):
    if sign not in _health_bar_map:
        _health_bar_map[sign] = HealthBarState()
    bar = _health_bar_map[sign]
    if horizontal:
        bar.draw_horizontal(max_hp, hp, pos, size, draw_list)
    else:
        bar.draw_vertical(max_hp, hp, pos, size, draw_list)
