import os, sys, struct, time
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off

W, H = 1360/2, 768/2

# 3 kez oku - degisiyor mu?
for i in range(3):
    game.update_matrix()
    raw = pm.read_memory(game.address.matrix, 64)
    flat = struct.unpack_from("<16f", raw)
    m = game.view.matrix

    lpawn = pm.read_u64(game.address.local_pawn)
    pos = pm.read_vec3(lpawn + off.Pos)
    x,y,z = pos

    # Row-major (mevcut)
    w_row = m[3][0]*x + m[3][1]*y + m[3][2]*z + m[3][3]
    if abs(w_row) > 0.01:
        sx = W + (m[0][0]*x+m[0][1]*y+m[0][2]*z+m[0][3])/w_row*W
        sy = H - (m[1][0]*x+m[1][1]*y+m[1][2]*z+m[1][3])/w_row*H
        print(f"[{i}] row-major W={w_row:.3f} -> ({sx:.0f},{sy:.0f})")

    # Flat dogrudan
    w2 = flat[12]*x + flat[13]*y + flat[14]*z + flat[15]
    if abs(w2) > 0.01:
        sx2 = W + (flat[0]*x+flat[1]*y+flat[2]*z+flat[3])/w2*W
        sy2 = H - (flat[4]*x+flat[5]*y+flat[6]*z+flat[7])/w2*H
        print(f"[{i}] flat[12..15] W={w2:.3f} -> ({sx2:.0f},{sy2:.0f})")

    print(f"     flat W row: {flat[12]:.3f} {flat[13]:.3f} {flat[14]:.3f} {flat[15]:.3f}")
    print(f"     m[3] row:   {m[3][0]:.3f} {m[3][1]:.3f} {m[3][2]:.3f} {m[3][3]:.3f}")
    time.sleep(0.5)
