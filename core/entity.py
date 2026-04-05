"""
Entity system - PlayerController, PlayerPawn, CEntity.
Mirrors C++ Entity.h / Entity.cpp.
"""
import struct
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

from .bone import CBone, BONE_JOINT_SIZE


@dataclass
class PlayerController:
    address: int = 0
    team_id: int = 0
    health: int = 0
    alive_status: int = 0
    pawn_handle: int = 0
    player_name: str = ""

    def update(self, address: int) -> bool:
        from .process_manager import process_mgr as pm
        from .offsets import offsets as off

        if not address:
            return False
        self.address = address

        self.health       = pm.read_i32(address + off.Health)
        self.alive_status = pm.read_i32(address + off.IsAlive)
        self.team_id      = pm.read_i32(address + off.TeamID)

        raw_name = pm.read_memory(address + off.iszPlayerName, 260)
        if raw_name:
            end = raw_name.find(b'\x00')
            self.player_name = raw_name[:end].decode(errors="ignore") if end != -1 else "Name_None"
        else:
            self.player_name = "Name_None"

        return True

    def get_pawn_address(self) -> int:
        from .process_manager import process_mgr as pm
        from .offsets import offsets as off
        from .game import game

        pawn_handle = pm.read_u32(self.address + off.PlayerPawn)
        if not pawn_handle:
            return 0
        self.pawn_handle = pawn_handle

        ges = pm.read_u64(game.address.entity_list)
        if not ges:
            return 0

        chunk_idx = (pawn_handle & 0x7FFF) >> 9
        ent_idx   = pawn_handle & 0x1FF

        chunk_ptr = pm.read_u64(ges + 0x10 + 8 * chunk_idx)
        if not chunk_ptr or chunk_ptr > 0x7FFFFFFFFFFF:
            return 0

        # CS2: pawn list uses 0x70 stride
        pawn_addr = pm.read_u64(chunk_ptr + 0x70 * ent_idx)
        if pawn_addr and 0x10000 < pawn_addr < 0x7FFFFFFFFFFF:
            return pawn_addr
        return 0


@dataclass
class PlayerPawn:
    address: int = 0
    bone_data: CBone = field(default_factory=CBone)
    view_angle: Tuple[float, float] = (0.0, 0.0)   # pitch, yaw
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    screen_pos: Optional[Tuple[float, float]] = None
    camera_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    weapon_name: str = ""
    shots_fired: int = 0
    aim_punch: Tuple[float, float] = (0.0, 0.0)
    health: int = 0
    team_id: int = 0
    fov: int = 90
    b_spotted_by_mask: int = 0
    f_flags: int = 0

    def update(self, address: int) -> bool:
        from .process_manager import process_mgr as pm
        from .offsets import offsets as off
        from .game import game

        if not address:
            return False
        self.address = address

        self.camera_pos  = pm.read_vec3(address + off.vecLastClipCameraPos)
        self.pos         = pm.read_vec3(address + off.Pos)
        self.view_angle  = pm.read_vec2(address + off.angEyeAngles)
        self.aim_punch   = pm.read_vec2(address + off.aimPunchAngle)
        self.shots_fired = pm.read_u32(address + off.iShotsFired)
        self.health      = pm.read_i32(address + off.CurrentHealth)
        self.team_id     = pm.read_i32(address + off.iTeamNum)
        self.f_flags     = pm.read_i32(address + off.fFlags)
        self.b_spotted_by_mask = pm.read_u64(address + off.bSpottedByMask)

        cam_svc = pm.read_u64(address + off.CameraServices)
        self.fov = pm.read_i32(cam_svc + off.iFovStart) if cam_svc else 90

        self._update_weapon_name(pm, off)
        self.bone_data.update(address, pm, off, game.view)

        self.screen_pos = game.view.world_to_screen(self.pos)
        return True

    def _update_weapon_name(self, pm, off):
        weapon_addr = pm.trace_address(self.address + off.pClippingWeapon, [0x10, 0x20, 0x0])
        if not weapon_addr:
            self.weapon_name = "Weapon_None"
            return
        raw = pm.read_memory(weapon_addr, 260)
        if not raw:
            self.weapon_name = "Weapon_None"
            return
        end = raw.find(b'\x00')
        name = raw[:end].decode(errors="ignore") if end != -1 else ""
        idx = name.find("_")
        self.weapon_name = name[idx + 1:] if idx != -1 and name else "Weapon_None"

    def get_weapon_name_only(self):
        """Lightweight weapon name update for background thread."""
        from .process_manager import process_mgr as pm
        from .offsets import offsets as off
        self._update_weapon_name(pm, off)


class CEntity:
    def __init__(self):
        self.controller = PlayerController()
        self.pawn = PlayerPawn()
        self.local_controller_index: int = 0
        # Temp scatter buffers
        self.temp_bone_raw: bytes = b''
        self.temp_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.temp_health: int = 0
        self.temp_view_angle: Tuple[float, float] = (0.0, 0.0)
        self.temp_spotted_mask: int = 0

    def update_controller(self, address: int) -> bool:
        return self.controller.update(address)

    def update_pawn(self, address: int) -> bool:
        return self.pawn.update(address)

    def is_alive(self) -> bool:
        return self.controller.alive_status == 1 and self.pawn.health > 0

    def is_in_screen(self) -> bool:
        from .game import game
        screen = game.view.world_to_screen(self.pawn.pos)
        if screen is None:
            self.pawn.screen_pos = None
            return False
        # Ekran siniri kontrolu - biraz margin ver
        sw, sh = game.view.screen_w, game.view.screen_h
        if screen[0] < -sw or screen[0] > sw * 2 or screen[1] < -sh or screen[1] > sh * 2:
            self.pawn.screen_pos = None
            return False
        self.pawn.screen_pos = screen
        return True

    def get_bone(self) -> CBone:
        return self.pawn.bone_data

    def apply_scatter_data(self, view):
        """Apply temp scatter-read data to pawn fields."""
        from .game import game
        if self.temp_bone_raw:
            self.pawn.bone_data.update_from_raw(self.temp_bone_raw, view)
        self.pawn.pos              = self.temp_pos
        self.pawn.health           = self.temp_health
        self.pawn.view_angle       = self.temp_view_angle
        self.pawn.b_spotted_by_mask = self.temp_spotted_mask
        self.pawn.screen_pos       = view.world_to_screen(self.pawn.pos)
