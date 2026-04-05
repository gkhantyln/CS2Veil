"""View angle write test."""
import os,sys,time,struct,ctypes
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_BASE); sys.path.insert(0, _BASE)

from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off
import win32con
user32 = ctypes.WinDLL("user32")

print("10 saniye - ALT, SHIFT veya SPACE'e bas...")
triggered = False
for _ in range(100):
    time.sleep(0.1)
    for vk,name in [(win32con.VK_LMENU,"Sol ALT"),(win32con.VK_LSHIFT,"Sol SHIFT"),(win32con.VK_SPACE,"SPACE")]:
        if bool(user32.GetAsyncKeyState(vk) & 0x8000):
            print(f"\nTus: {name} (VK={hex(vk)})")
            lp = pm.read_u64(game.address.local_pawn)
            if not lp:
                print("LocalPawn okunamadi!"); continue
            cur = pm.read_vec2(lp + off.angEyeAngles)
            print(f"Mevcut: pitch={cur[0]:.2f} yaw={cur[1]:.2f}")
            print(f"ViewAngle addr: 0x{game.address.view_angle:X}")
            # Yaz
            ok = game.set_view_angle(cur[0], cur[1] + 10.0)
            print(f"Write result: {ok}")
            time.sleep(0.1)
            after = pm.read_vec2(lp + off.angEyeAngles)
            print(f"Sonra: pitch={after[0]:.2f} yaw={after[1]:.2f}")
            print(f"Degisim: {after[1]-cur[1]:.2f} (beklenen: ~10)")
            triggered = True
            break
    if triggered: break

if not triggered:
    print("Hic tus algilanmadi!")
    # Manuel test - tus olmadan yaz
    lp = pm.read_u64(game.address.local_pawn)
    cur = pm.read_vec2(lp + off.angEyeAngles)
    print(f"Manuel test - mevcut: {cur}")
    ok = game.set_view_angle(cur[0], cur[1] + 5.0)
    print(f"Write: {ok}")
    time.sleep(0.1)
    after = pm.read_vec2(lp + off.angEyeAngles)
    print(f"Sonra: {after}")
