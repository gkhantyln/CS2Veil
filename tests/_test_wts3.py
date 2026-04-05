"""
WorldToScreen dogru formul bul.
Calistir, bir dusmana bak, hangi formul mantikli koordinat veriyor?
"""
import os, sys, struct, time
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off
from core.bone import BONEINDEX, BONE_JOINT_SIZE

W, H = 1360, 768

print("3 saniye bekle, bir dusmana bak...")
time.sleep(3)

game.update_matrix()
raw = pm.read_memory(game.address.matrix, 64)
flat = struct.unpack_from("<16f", raw)

print("Matrix:")
for i in range(4):
    print(f"  row[{i}]: {[f'{v:.3f}' for v in flat[i*4:(i+1)*4]]}")

# Local player
lp = pm.read_u64(game.address.local_pawn)
lpos = pm.read_vec3(lp + off.Pos)
print(f"\nLocal pos: {lpos}")

# Tum entity'leri bul
ges = pm.read_u64(game.address.entity_list)
game.update_entity_list_entry()
base = game.address.entity_list_entry
lc = pm.read_u64(game.address.local_controller)

def wts(flat, pos, w_row, x_row, y_row, sw, sh):
    x,y,z = pos
    w = flat[w_row*4]*x + flat[w_row*4+1]*y + flat[w_row*4+2]*z + flat[w_row*4+3]
    if abs(w) < 0.01: return None
    sx = sw/2 + (flat[x_row*4]*x + flat[x_row*4+1]*y + flat[x_row*4+2]*z + flat[x_row*4+3]) / w * sw/2
    sy = sh/2 - (flat[y_row*4]*x + flat[y_row*4+1]*y + flat[y_row*4+2]*z + flat[y_row*4+3]) / w * sh/2
    return (sx, sy, w)

print("\n--- Entity'ler ve farkli formul sonuclari ---")
for ci in range(2):
    cp = pm.read_u64(base + ci*0x8)
    if not cp or cp > 0x7FFFFFFFFFFF: continue
    for ei in range(512):
        ctrl = pm.read_u64(cp + ei*0x8)
        if not ctrl or ctrl > 0x7FFFFFFFFFFF or ctrl < 0x10000 or ctrl == lc: continue
        if pm.read_i32(ctrl + off.IsAlive) != 1: continue
        nr = pm.read_memory(ctrl + off.iszPlayerName, 32)
        if not nr: continue
        e = nr.find(b'\x00'); name = nr[:e].decode(errors="ignore") if e!=-1 else ""
        if not name: continue
        ph = pm.read_u32(ctrl + off.PlayerPawn)
        if not ph: continue
        c2=(ph&0x7FFF)>>9; e3=ph&0x1FF
        ch=pm.read_u64(ges+0x10+8*c2)
        if not ch: continue
        pawn=pm.read_u64(ch+0x70*e3)
        if not pawn or pawn>0x7FFFFFFFFFFF: continue
        hp=pm.read_i32(pawn+off.CurrentHealth)
        if hp<=0: continue
        pos=pm.read_vec3(pawn+off.Pos)

        # Head bone
        sc=pm.read_u64(pawn+off.GameSceneNode)
        head_pos=None
        if sc:
            ba=pm.read_u64(sc+off.BoneArray)
            if ba:
                rb=pm.read_memory(ba+BONEINDEX.head*BONE_JOINT_SIZE,12)
                if rb: head_pos=struct.unpack_from("<fff",rb)

        print(f"\n{name} HP={hp} pos={[f'{v:.0f}' for v in pos]}")

        # Tum kombinasyonlari dene - W pozitif olmali, koordinatlar ekranda olmali
        best = []
        for wr in range(4):
            for xr in range(4):
                for yr in range(4):
                    if wr==xr or wr==yr or xr==yr: continue
                    r = wts(flat, pos, wr, xr, yr, W, H)
                    if r and 0<r[0]<W and 0<r[1]<H and r[2]>0:
                        best.append((wr,xr,yr,r[0],r[1],r[2]))

        if best:
            print(f"  Ekranda gorunen formuller (W>0):")
            for b in best[:5]:
                print(f"    W=row[{b[0]}] X=row[{b[1]}] Y=row[{b[2]}] -> ({b[3]:.0f},{b[4]:.0f}) W={b[5]:.2f}")
        else:
            print(f"  Hic ekranda degil (kamera arkasinda olabilir)")
