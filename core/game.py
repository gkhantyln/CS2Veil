"""
CGame - address management, matrix, view angle write.
Mirrors C++ Game.h / Game.cpp.
"""
import struct
from dataclasses import dataclass

from .view import CView


@dataclass
class GameAddresses:
    client_dll:       int = 0
    match_dll:        int = 0
    entity_list:      int = 0
    matrix:           int = 0
    view_angle:       int = 0
    entity_list_entry:int = 0
    local_controller: int = 0
    local_pawn:       int = 0
    force_jump:       int = 0
    global_vars:      int = 0


class CGame:
    def __init__(self):
        self.address = GameAddresses()
        self.view = CView()

    def init_address(self) -> bool:
        from .process_manager import process_mgr as pm
        from .offsets import offsets as off

        self.address.client_dll = pm.get_module_base("client.dll")
        self.address.match_dll  = pm.get_module_base("matchmaking.dll")

        if not self.address.client_dll:
            return False

        base = self.address.client_dll
        self.address.entity_list      = base + off.EntityList
        self.address.matrix           = base + off.Matrix
        self.address.view_angle       = base + off.ViewAngle
        self.address.local_controller = base + off.LocalPlayerController
        self.address.local_pawn       = base + off.LocalPlayerPawn
        self.address.force_jump       = base + off.ForceJump
        self.address.global_vars      = base + off.GlobalVars

        return True

    def update_entity_list_entry(self) -> bool:
        from .process_manager import process_mgr as pm

        ges = pm.read_u64(self.address.entity_list)
        if not ges or ges > 0x7FFFFFFFFFFF:
            return False
        # Chunk array = GES + 0x10
        chunk_array = ges + 0x10
        # Dogrula
        first_chunk = pm.read_u64(chunk_array)
        if not first_chunk or first_chunk > 0x7FFFFFFFFFFF:
            return False
        self.address.entity_list_entry = chunk_array
        return True

    def update_matrix(self) -> bool:
        from .process_manager import process_mgr as pm

        raw = pm.read_memory(self.address.matrix, 64)
        if not raw:
            return False
        flat = struct.unpack_from("<16f", raw)
        for row in range(4):
            for col in range(4):
                self.view.matrix[row][col] = flat[row * 4 + col]
        return True

    def set_view_angle(self, pitch: float, yaw: float) -> bool:
        from .process_manager import process_mgr as pm
        from .offsets import offsets as off
        import struct
        # v_angle: C_BasePlayerPawn + 0x1490 - direkt pawn'a yaz
        lp = pm.read_u64(self.address.local_pawn)
        if not lp:
            return False
        data = struct.pack("<ff", pitch, yaw)
        # Hem v_angle hem dwViewAngles'a yaz
        r1 = pm.write_memory(lp + 0x1490, data)
        r2 = pm.write_memory(self.address.view_angle, data)
        return r1 or r2

    def set_force_jump(self, value: int) -> bool:
        from .process_manager import process_mgr as pm
        return pm.write_memory(self.address.force_jump, struct.pack("<I", value))

    def get_map_name(self) -> str:
        from .process_manager import process_mgr as pm
        from .offsets import offsets as off

        if not self.address.match_dll:
            return ""
        map_ptr = pm.read_u64(self.address.match_dll + 0x001D2300)
        if not map_ptr:
            return ""
        return pm.read_string(map_ptr + 0x4, 32)


# Singleton
game = CGame()
