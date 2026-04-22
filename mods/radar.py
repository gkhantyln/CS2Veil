"""
Radar mod - mirrors C++ Radar.cpp / Base_Radar.
Renders via imgui draw list.
"""
import math
from typing import List, Tuple, Optional
import imgui

from utils.maps_data import map_state, SPLIT_MAPS


class RadarPoint:
    def __init__(self, pos: Tuple[float, float], same_team: int,
                 local_yaw: float, hp: float, is_bomb: int = 0):
        self.pos       = pos        # (minimap_x, minimap_y)
        self.same_team = same_team  # 0=enemy 1=ally 2=local
        self.local_yaw = local_yaw
        self.hp        = hp
        self.is_bomb   = is_bomb


class RadarConfig:
    def __init__(self):
        self.enabled    = False
        self.size_type  = 0       # 0=Small 1=Big
        self.radar_size = 300.0
        self.line_length= 6
        self.circle_size= 2.0

    def apply_size(self):
        if self.size_type == 0:
            self.circle_size = 2
            self.line_length = 6
            self.radar_size  = 300
        else:
            self.circle_size = 5
            self.line_length = 10
            self.radar_size  = 600
        map_state.radar_size  = self.radar_size
        map_state.line_length = self.line_length
        map_state.circle_size = self.circle_size


radar_config = RadarConfig()
_points: List[RadarPoint] = []


def add_point(local_pos, local_yaw: float, entity_pos, color, yaw: float = 0.0,
              same_team: int = 1, hp: float = 100.0, is_bomb: int = 0):
    ex, ey, ez = entity_pos
    minimap = map_state.world_to_minimap_split(ex, ey, ez)
    _points.append(RadarPoint(minimap, same_team, local_yaw, hp, is_bomb))


def render_radar(draw_list, window_pos: Tuple[float, float]):
    global _points
    rs = map_state.radar_size
    wx, wy = window_pos

    # Background map texture
    if map_state.texture_id:
        draw_list.add_image(map_state.texture_id,
                            wx, wy, wx + rs, wy + rs)
    draw_list.add_rect_filled(wx, wy, wx + rs, wy + rs,
                               imgui.get_color_u32_rgba(1, 1, 1, 0.04))

    ll = map_state.line_length
    cs = map_state.circle_size

    for pt in _points:
        px = pt.pos[0] + wx
        py = pt.pos[1] + wy

        if pt.same_team == 1:
            col = imgui.get_color_u32_rgba(0, 1, 0, 1)
            tri_col = col
        elif pt.same_team == 0:
            col = imgui.get_color_u32_rgba(1, 0, 0, 1)
            tri_col = col
            draw_list.add_text(px - 10, py + 2,
                                imgui.get_color_u32_rgba(0, 1, 0, 1),
                                str(int(pt.hp)))
        else:
            col = imgui.get_color_u32_rgba(0, 0.89, 0.82, 1)
            tri_col = col

        radian = pt.local_yaw * (math.pi / 180)
        top_x  = px + math.sin(radian) * ll
        top_y  = py + math.cos(radian) * ll
        left_x = px + math.sin(radian + math.pi / 3) * ll / 2
        left_y = py + math.cos(radian + math.pi / 3) * ll / 2
        right_x= px + math.sin(radian - math.pi / 3) * ll / 2
        right_y= py + math.cos(radian - math.pi / 3) * ll / 2

        draw_list.add_circle(px, py, cs, col, 0, 5)
        draw_list.add_triangle(left_x, left_y, right_x, right_y,
                                top_x, top_y, tri_col, 3)

    _points.clear()
