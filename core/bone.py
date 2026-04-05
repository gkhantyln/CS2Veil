"""
Bone system - mirrors CBone, BoneJointData, BoneJointPos, BONEINDEX.
"""
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class BONEINDEX:
    pelvis      = 0
    spine_2     = 2
    spine_1     = 4
    neck_0      = 5
    head        = 6
    arm_upper_L = 8
    arm_lower_L = 9
    hand_L      = 10
    arm_upper_R = 13
    arm_lower_R = 14
    hand_R      = 15
    leg_upper_L = 22
    leg_lower_L = 23
    ankle_L     = 24
    leg_upper_R = 25
    leg_lower_R = 26
    ankle_R     = 27


# Bone connection chains for skeleton drawing
BONE_CHAINS = [
    [BONEINDEX.head, BONEINDEX.neck_0, BONEINDEX.spine_2, BONEINDEX.pelvis],          # trunk
    [BONEINDEX.neck_0, BONEINDEX.arm_upper_L, BONEINDEX.arm_lower_L, BONEINDEX.hand_L],  # left arm
    [BONEINDEX.neck_0, BONEINDEX.arm_upper_R, BONEINDEX.arm_lower_R, BONEINDEX.hand_R],  # right arm
    [BONEINDEX.pelvis, BONEINDEX.leg_upper_L, BONEINDEX.leg_lower_L, BONEINDEX.ankle_L], # left leg
    [BONEINDEX.pelvis, BONEINDEX.leg_upper_R, BONEINDEX.leg_lower_R, BONEINDEX.ankle_R], # right leg
]

BONE_JOINT_SIZE = 0x20  # sizeof(BoneJointData) = Vec3(12) + pad(0x14) = 32 bytes


@dataclass
class BoneJointPos:
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    screen_pos: Optional[Tuple[float, float]] = None
    is_visible: bool = False


class CBone:
    def __init__(self):
        self.bone_array_address: int = 0
        self.bone_list: List[BoneJointPos] = []

    def update(self, pawn_address: int, process_mgr, offsets, view) -> bool:
        from .offsets import offsets as off
        from .process_manager import process_mgr as pm

        scene_node = pm.read_u64(pawn_address + off.GameSceneNode)
        if not scene_node:
            return False

        bone_arr_addr = pm.read_u64(scene_node + off.BoneArray)
        if not bone_arr_addr:
            return False

        self.bone_array_address = bone_arr_addr

        raw = pm.read_memory(bone_arr_addr, 30 * BONE_JOINT_SIZE)
        if not raw:
            return False

        self.bone_list = []
        for i in range(30):
            offset = i * BONE_JOINT_SIZE
            x, y, z = struct.unpack_from("<fff", raw, offset)
            screen = view.world_to_screen((x, y, z))
            self.bone_list.append(BoneJointPos(
                pos=(x, y, z),
                screen_pos=screen,
                is_visible=screen is not None
            ))

        return len(self.bone_list) > 0

    def update_from_raw(self, raw_data: bytes, view) -> bool:
        """Update bone positions from pre-read scatter data."""
        self.bone_list = []
        for i in range(30):
            offset = i * BONE_JOINT_SIZE
            if offset + 12 > len(raw_data):
                break
            x, y, z = struct.unpack_from("<fff", raw_data, offset)
            screen = view.world_to_screen((x, y, z))
            self.bone_list.append(BoneJointPos(
                pos=(x, y, z),
                screen_pos=screen,
                is_visible=screen is not None
            ))
        return len(self.bone_list) > 0
