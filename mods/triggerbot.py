"""
TriggerBot mod - mirrors C++ TriggerBot.cpp.
"""
import time
import win32con

from core.entity import CEntity
from utils.kmbox import kmbox

HOTKEY_LIST = [
    win32con.VK_LMENU,     # 0 - Sol ALT
    win32con.VK_RMENU,     # 1 - Sağ ALT
    win32con.VK_RBUTTON,   # 2 - Sağ Tık
    win32con.VK_XBUTTON1,  # 3 - Yan Tuş 1
    win32con.VK_XBUTTON2,  # 4 - Yan Tuş 2
    win32con.VK_CAPITAL,   # 5 - Caps Lock
    win32con.VK_LSHIFT,    # 6 - Sol Shift
    win32con.VK_LCONTROL,  # 7 - Sol Ctrl
]

HOTKEY_NAMES = [
    "Sol ALT",
    "Sag ALT",
    "Sag Tik",
    "Yan Tus 1",
    "Yan Tus 2",
    "Caps Lock",
    "Sol Shift",
    "Sol Ctrl",
]


class TriggerConfig:
    def __init__(self):
        self.enabled      = True
        self.hotkey_index = 4          # CAPITAL
        self.hotkey       = win32con.VK_CAPITAL
        self.mode         = 0          # 0=OnKey 1=Always
        self.delay_ms     = 90

    def apply_hotkey(self):
        if 0 <= self.hotkey_index < len(HOTKEY_LIST):
            self.hotkey = HOTKEY_LIST[self.hotkey_index]


trigger_config = TriggerConfig()
_last_trigger_time: float = 0.0


def run_triggerbot(local: CEntity):
    global _last_trigger_time
    from core.process_manager import process_mgr as pm
    from core.offsets import offsets as off
    from core.game import game
    from core.entity import CEntity as CE

    handle = pm.read_u32(local.pawn.address + off.iIDEntIndex)
    if not handle or handle == 0xFFFFFFFF:
        return

    entity_list = game.address.entity_list
    list_entry = pm.trace_address(entity_list, [0x8 * (handle >> 9) + 0x10, 0x0])
    if not list_entry:
        return

    pawn_addr = pm.read_u64(list_entry + 0x78 * (handle & 0x1FF))
    if not pawn_addr:
        return

    target = CE()
    if not target.update_pawn(pawn_addr):
        return

    from ui.menu import menu_config
    if menu_config.team_check:
        allow = local.pawn.team_id != target.pawn.team_id and target.pawn.health > 0
    else:
        allow = target.pawn.health > 0

    if not allow:
        return

    now = time.monotonic()
    if now - _last_trigger_time < trigger_config.delay_ms / 1000.0:
        return

    if not pm.is_key_down(win32con.VK_LBUTTON):
        kmbox.left_click()

    _last_trigger_time = now
