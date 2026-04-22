"""
Mouse/Keyboard controller - SendInput backend.
Replaces KmBox hardware with Windows SendInput API.
No external hardware required.
"""
import ctypes
import ctypes.wintypes as wt
import time
import json
import math

user32 = ctypes.WinDLL("user32", use_last_error=True)

# SendInput structures
INPUT_MOUSE    = 0
MOUSEEVENTF_MOVE        = 0x0001
MOUSEEVENTF_LEFTDOWN    = 0x0002
MOUSEEVENTF_LEFTUP      = 0x0004
MOUSEEVENTF_RIGHTDOWN   = 0x0008
MOUSEEVENTF_RIGHTUP     = 0x0010
MOUSEEVENTF_ABSOLUTE    = 0x8000

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          wt.LONG),
        ("dy",          wt.LONG),
        ("mouseData",   wt.DWORD),
        ("dwFlags",     wt.DWORD),
        ("time",        wt.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wt.DWORD),
        ("_input", _INPUT_UNION),
    ]

def _send_mouse_move(dx: int, dy: int):
    # Once SendInput dene
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp._input.mi.dx      = int(dx)
    inp._input.mi.dy      = int(dy)
    inp._input.mi.dwFlags = MOUSEEVENTF_MOVE
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    # CS2 raw input icin mouse_event de gonder (eski API, bazi oyunlarda calisir)
    user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)

def _send_mouse_click(down: bool, right: bool = False):
    inp = INPUT()
    inp.type = INPUT_MOUSE
    if right:
        inp._input.mi.dwFlags = MOUSEEVENTF_RIGHTDOWN if down else MOUSEEVENTF_RIGHTUP
    else:
        inp._input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


class KmBoxManager:
    """
    Unified mouse controller.
    Uses SendInput (no hardware needed).
    Config type is ignored - always uses SendInput.
    """
    def __init__(self):
        self.type = "sendinput"

    def init_from_config(self, config_path: str = "kmbox.json") -> bool:
        # Try to read config but don't fail if missing
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            self.type = cfg.get("type", "sendinput")
        except FileNotFoundError:
            pass  # No config needed for SendInput

        # Always fall back to SendInput if KmBox not available
        if self.type in ("net", "b"):
            if not self._try_kmbox(config_path):
                print("[ warn ] KmBox not available, falling back to SendInput")
                self.type = "sendinput"

        print(f"[ info ] Mouse controller: {self.type}")
        return True

    def _try_kmbox(self, config_path: str) -> bool:
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            if cfg.get("type") == "net":
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.0)
                s.connect((cfg["ip"], cfg["port"]))
                s.close()
                self._kmbox_net_cfg = cfg
                return True
        except Exception:
            pass
        return False

    def move(self, x: float, y: float):
        if abs(x) < 0.5 and abs(y) < 0.5:
            return
        _send_mouse_move(int(x), int(y))

    def move_auto(self, x: float, y: float, ms: float):
        """Smooth move split into steps over ms milliseconds."""
        if abs(x) < 0.5 and abs(y) < 0.5:
            return
        steps = max(1, int(ms / 2))
        dx = x / steps
        dy = y / steps
        delay = ms / 1000.0 / steps
        for _ in range(steps):
            _send_mouse_move(int(dx), int(dy))
            if delay > 0.001:
                time.sleep(delay)

    def left_click(self):
        _send_mouse_click(True)
        time.sleep(0.01)
        _send_mouse_click(False)

    def left_down(self):
        _send_mouse_click(True)

    def left_up(self):
        _send_mouse_click(False)


# Singleton
kmbox = KmBoxManager()
