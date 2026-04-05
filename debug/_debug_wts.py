import os, sys, struct
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off

game.update_matrix()
raw = pm.read_memory(game.address.matrix, 64)
flat = struct.unpack_from("<16f", raw)

lpawn = pm.read_u64(game.address.local_pawn)
pos = pm.read_vec3(lpawn + off.Pos)
x,y,z = pos
W, H = 1360/2, 768/2

print(f"pos: {pos}")
print(f"flat: {[f'{v:.3f}' for v in flat]}")
print()

# Tum kombinasyonlari dene - W satiri x X satiri x Y satiri
for wi in range(4):
    w = flat[wi*4]*x + flat[wi*4+1]*y + flat[wi*4+2]*z + flat[wi*4+3]
    if abs(w) < 0.01: continue
    for xi in range(4):
        if xi == wi: continue
        for yi in range(4):
            if yi == wi or yi == xi: continue
            sx = W + (flat[xi*4]*x+flat[xi*4+1]*y+flat[xi*4+2]*z+flat[xi*4+3])/w*W
            sy = H - (flat[yi*4]*x+flat[yi*4+1]*y+flat[yi*4+2]*z+flat[yi*4+3])/w*H
            if 0 < sx < 1360 and 0 < sy < 768:
                print(f"W=row[{wi}]={w:.2f}  X=row[{xi}]  Y=row[{yi}]  -> ({sx:.0f},{sy:.0f})  <-- EKRANDA")
