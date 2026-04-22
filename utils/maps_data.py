"""
Map metadata for radar rendering.
Mirrors C++ mapsdata.h (without embedded PNG bytes - loads from files).
"""
import os
from typing import Dict, List, Optional

# { map_name: [scale, offset_x, offset_y, (split_z, split_x, split_y)] }
MAPS_DATA: Dict[str, List] = {
    "de_mirage":   [2.5,  -3420, -3263],
    "de_overpass": [2.6,  -3550, -4840],
    "de_inferno":  [2.5,  -1213, -2170],
    "de_anubis":   [2.6,  -2004, -2770],
    "de_dust2":    [2.2,  -1280, -2500],
    "de_ancient":  [2.2,  -2650, -2650],
    "de_vertigo":  [2.55, -3925, -4010, 11700, -1675, -3960],
    "de_nuke":     [1.764,-6060, -3350,  -500, -2710, -3350],
}

SPLIT_MAPS = {"de_nuke", "de_vertigo"}


class MapState:
    def __init__(self):
        self.current_map: str = ""
        self.radar_size: float = 300.0
        self.line_length: int = 6
        self.circle_size: float = 2.0
        self.img_w: int = 1024
        self.img_h: int = 1024

        self.map_zoom: float = 1.0
        self.map_offset_x: float = 0.0
        self.map_offset_y: float = 0.0
        self.split_z: float = 0.0
        self.split_x: float = 0.0
        self.split_y: float = 0.0

        # imgui texture id (set by renderer)
        self.texture_id = None
        self._texture_data: Optional[bytes] = None

    def update_map(self, map_name: str, texture_loader=None):
        if map_name == self.current_map:
            return
        self.current_map = map_name
        if map_name == "<empty>" or not map_name:
            self.texture_id = None
            return

        data = MAPS_DATA.get(map_name)
        if data:
            self.map_zoom     = data[0]
            self.map_offset_x = data[1]
            self.map_offset_y = data[2]
            if map_name in SPLIT_MAPS and len(data) >= 6:
                self.split_z = data[3]
                self.split_x = data[4]
                self.split_y = data[5]

        # Load PNG from maps/ folder
        if texture_loader:
            png_path = os.path.join("maps", f"{map_name}.png")
            if os.path.exists(png_path):
                self.texture_id = texture_loader(png_path)
            else:
                print(f"[ radar ] Map image not found: {png_path}")
                self.texture_id = None

    def world_to_minimap(self, x: float, y: float) -> tuple:
        import math
        scale = self.map_zoom
        rs    = self.radar_size
        img_x = int((x - self.map_offset_x) * rs / (self.img_w * scale * 2))
        img_y = int((y - self.map_offset_y) * rs / (self.img_h * scale * 2))
        return (img_x, img_y)

    def world_to_minimap_split(self, pos_x: float, pos_y: float, pos_z: float) -> tuple:
        if self.current_map in SPLIT_MAPS and pos_z < self.split_z:
            return self.world_to_minimap_with_offset(pos_y, pos_x, self.split_x, self.split_y)
        return self.world_to_minimap_with_offset(pos_y, pos_x, self.map_offset_x, self.map_offset_y)

    def world_to_minimap_with_offset(self, x: float, y: float, ox: float, oy: float) -> tuple:
        rs    = self.radar_size
        scale = self.map_zoom
        img_x = int((x - ox) * rs / (self.img_w * scale * 2))
        img_y = int((y - oy) * rs / (self.img_h * scale * 2))
        return (img_x, img_y)


# Singleton
map_state = MapState()
