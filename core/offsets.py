"""
Offset loader - reads offsets.json and client.dll.json
Mirrors C++ Offset namespace.
"""
import json
from dataclasses import dataclass, field


@dataclass
class GlobalVarOffsets:
    RealTime:        int = 0x00
    FrameCount:      int = 0x04
    MaxClients:      int = 0x10
    IntervalPerTick: int = 0x14
    CurrentTime:     int = 0x2C
    CurrentTime2:    int = 0x30
    TickCount:       int = 0x40
    IntervalPerTick2:int = 0x44
    CurrentNetchan:  int = 0x0048
    CurrentMap:      int = 0x0180
    CurrentMapName:  int = 0x0188


class Offsets:
    # client.dll globals
    EntityList:           int = 0
    Matrix:               int = 0
    ViewAngle:            int = 0
    LocalPlayerController:int = 0
    LocalPlayerPawn:      int = 0
    ForceJump:            int = 0
    GlobalVars:           int = 0

    # Controller
    Health:        int = 0
    TeamID:        int = 0
    IsAlive:       int = 0
    PlayerPawn:    int = 0
    iszPlayerName: int = 0

    # Pawn
    Pos:                  int = 0
    MaxHealth:            int = 0
    CurrentHealth:        int = 0
    GameSceneNode:        int = 0
    BoneArray:            int = 0
    angEyeAngles:         int = 0
    vecLastClipCameraPos: int = 0
    pClippingWeapon:      int = 0
    iShotsFired:          int = 0
    flFlashDuration:      int = 0
    aimPunchAngle:        int = 0
    aimPunchCache:        int = 0
    iIDEntIndex:          int = 0
    iTeamNum:             int = 0
    CameraServices:       int = 0
    iFovStart:            int = 0
    fFlags:               int = 0
    vecVelocity:          int = 0
    bSpottedByMask:       int = 0

    GlobalVar: GlobalVarOffsets = field(default_factory=GlobalVarOffsets)

    def __init__(self):
        self.GlobalVar = GlobalVarOffsets()

    def update(self, offsets_path: str = "offsets.json", client_path: str = "client.dll.json") -> bool:
        import os
        missing = [p for p in (offsets_path, client_path) if not os.path.exists(p)]
        if missing:
            for p in missing:
                print(f"[ error ] File not found: {p}")
            print("[ info ] Download offsets from: https://github.com/a2x/cs2-dumper/releases")
            print("[ info ] Place offsets.json and client.dll.json in the CS2_Python/ folder")
            return False

        try:
            with open(offsets_path, "r") as f:
                off = json.load(f)
            with open(client_path, "r") as f:
                cli = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ error ] Failed to parse JSON: {e}")
            return False

        # New format: off["client.dll"]["dwEntityList"] = int
        cd = off.get("client.dll", {})
        self.EntityList            = cd.get("dwEntityList", 0)
        self.Matrix                = cd.get("dwViewMatrix", 0)
        self.ViewAngle             = cd.get("dwViewAngles", 0)
        self.LocalPlayerController = cd.get("dwLocalPlayerController", 0)
        self.LocalPlayerPawn       = cd.get("dwLocalPlayerPawn", 0)
        self.ForceJump             = cd.get("dwForceJump", 0)
        self.GlobalVars            = cd.get("dwGlobalVars", 0)

        # New format: cli["client.dll"]["classes"]["ClassName"]["fields"]["field"] = int
        def field(cls: str, name: str) -> int:
            return cli.get("client.dll", {}).get("classes", {}).get(cls, {}).get("fields", {}).get(name, 0)

        self.Health        = field("C_BaseEntity", "m_iHealth")
        self.TeamID        = field("C_BaseEntity", "m_iTeamNum")
        self.IsAlive       = field("CCSPlayerController", "m_bPawnIsAlive")
        self.PlayerPawn    = field("CCSPlayerController", "m_hPlayerPawn")
        self.iszPlayerName = field("CBasePlayerController", "m_iszPlayerName")

        self.Pos                  = field("C_BasePlayerPawn", "m_vOldOrigin")
        self.MaxHealth            = field("C_BaseEntity", "m_iMaxHealth")
        self.CurrentHealth        = field("C_BaseEntity", "m_iHealth")
        self.GameSceneNode        = field("C_BaseEntity", "m_pGameSceneNode")
        self.BoneArray            = 0x1E0  # GameSceneNode + 0x1E0 (test ile dogrulanmis)
        self.angEyeAngles         = field("C_CSPlayerPawn", "m_angEyeAngles")
        self.vecLastClipCameraPos = field("C_CSPlayerPawn", "m_vecLastClipCameraPos")
        self.pClippingWeapon      = field("C_CSPlayerPawnBase", "m_pClippingWeapon")
        self.iShotsFired          = field("C_CSPlayerPawnBase", "m_iShotsFired")
        self.flFlashDuration      = field("C_CSPlayerPawnBase", "m_flFlashDuration")
        self.aimPunchAngle        = field("C_CSPlayerPawn", "m_aimPunchAngle")
        self.aimPunchCache        = field("C_CSPlayerPawn", "m_aimPunchCache")
        self.iIDEntIndex          = field("C_CSPlayerPawnBase", "m_iIDEntIndex")
        self.iTeamNum             = field("C_BaseEntity", "m_iTeamNum")
        self.CameraServices       = field("C_BasePlayerPawn", "m_pCameraServices")
        self.iFovStart            = field("CCSPlayerBase_CameraServices", "m_iFOVStart")
        self.fFlags               = field("C_BaseEntity", "m_fFlags")
        self.vecVelocity          = field("C_BasePlayerPawn", "m_vecVelocity")

        m_entity_spotted = field("C_CSPlayerPawnBase", "m_entitySpottedState")
        m_spotted_mask   = field("EntitySpottedState_t", "m_bSpottedByMask")
        self.bSpottedByMask = m_entity_spotted + m_spotted_mask

        # Validate critical offsets
        missing = [k for k, v in {
            "EntityList": self.EntityList, "Matrix": self.Matrix,
            "Health": self.Health, "GameSceneNode": self.GameSceneNode,
        }.items() if v == 0]
        if missing:
            print(f"[ warn ] Some offsets are zero: {missing}")

        print(f"[ info ] Offsets loaded (EntityList=0x{self.EntityList:X}, Matrix=0x{self.Matrix:X})")
        return True


# Singleton
offsets = Offsets()
