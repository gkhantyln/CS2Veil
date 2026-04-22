"""
Bone system - CS2 skeleton indices (Apr 2026 update).
"""
import struct
from dataclasses import dataclass
from typing import List, Optional, Tuple


class BONEINDEX:
    pelvis      = 1   # bel — bacakların birleştiği nokta
    spine_0     = 2
    spine_1     = 3
    spine_2     = 4
    spine_3     = 5
    neck_0      = 6
    head        = 7
    arm_upper_R = 9
    arm_lower_R = 10
    hand_R      = 11
    arm_upper_L = 13
    arm_lower_L = 14
    hand_L      = 15
    leg_upper_L = 17
    leg_lower_L = 18
    ankle_L     = 19
    leg_upper_R = 21
    leg_lower_R = 22
    ankle_R     = 22


# Bone connection chains
BONE_CHAINS = [
    [BONEINDEX.head,   BONEINDEX.neck_0,      BONEINDEX.spine_3,     BONEINDEX.spine_1, BONEINDEX.pelvis],
    [BONEINDEX.neck_0, BONEINDEX.arm_upper_R, BONEINDEX.arm_lower_R, BONEINDEX.hand_R],
    [BONEINDEX.neck_0, BONEINDEX.arm_upper_L, BONEINDEX.arm_lower_L, BONEINDEX.hand_L],
    [BONEINDEX.pelvis, BONEINDEX.leg_upper_L, BONEINDEX.leg_lower_L, BONEINDEX.ankle_L],
    [BONEINDEX.pelvis, BONEINDEX.leg_upper_R, BONEINDEX.leg_lower_R],
]

# Aim hedef bone listesi
AIM_BONE_NAMES = ["Kafa", "Boyun", "Omuz", "Gogus", "Govde", "Pelvis"]
AIM_BONE_INDEX = [
    BONEINDEX.head,
    BONEINDEX.neck_0,
    BONEINDEX.spine_3,
    BONEINDEX.spine_2,
    BONEINDEX.spine_1,
    BONEINDEX.pelvis,
]

BONE_JOINT_SIZE = 0x20  # sizeof(BoneJointData) = 32 bytes


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
        raw = pm.read_memory(bone_arr_addr, 32 * BONE_JOINT_SIZE)
        if not raw:
            return False
        self.bone_list = []
        for i in range(32):
            offset = i * BONE_JOINT_SIZE
            if offset + 12 > len(raw):
                break
            x, y, z = struct.unpack_from("<fff", raw, offset)
            screen = view.world_to_screen((x, y, z))
            self.bone_list.append(BoneJointPos(pos=(x, y, z), screen_pos=screen, is_visible=screen is not None))
        return len(self.bone_list) > 0

    def update_from_raw(self, raw_data: bytes, view) -> bool:
        self.bone_list = []
        for i in range(32):
            offset = i * BONE_JOINT_SIZE
            if offset + 12 > len(raw_data):
                break
            x, y, z = struct.unpack_from("<fff", raw_data, offset)
            screen = view.world_to_screen((x, y, z))
            self.bone_list.append(BoneJointPos(pos=(x, y, z), screen_pos=screen, is_visible=screen is not None))
        return len(self.bone_list) > 0
