"""Maçtayken entity thread'in ne yaptığını göster."""
import os, sys, time, struct
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off

W, H = 1360, 768
game.view.set_screen_size(float(W), float(H))
game.update_matrix()

print("=== ADRES KONTROL ===")
print(f"client.dll:    0x{game.address.client_dll:X}")
print(f"entity_list:   0x{game.address.entity_list:X}")
print(f"local_ctrl:    0x{pm.read_u64(game.address.local_controller):X}")
print(f"local_pawn:    0x{pm.read_u64(game.address.local_pawn):X}")

ges = pm.read_u64(game.address.entity_list)
print(f"\nGES (GameEntitySystem): 0x{ges:X}")

# GES+0x10 = chunk array
chunk_array = ges + 0x10
print(f"chunk_array (GES+0x10): 0x{chunk_array:X}")

# entity_list_entry
ok = game.update_entity_list_entry()
print(f"update_entity_list_entry: ok={ok}  entry=0x{game.address.entity_list_entry:X}")

# Chunk'lari listele
print("\n=== CHUNK LISTESI ===")
for ci in range(8):
    cp = pm.read_u64(chunk_array + ci * 0x8)
    if cp and 0x10000 < cp < 0x7FFFFFFFFFFF:
        print(f"  chunk[{ci}] = 0x{cp:X}")

# Local player
lctrl = pm.read_u64(game.address.local_controller)
lpawn = pm.read_u64(game.address.local_pawn)
lteam = pm.read_i32(lctrl + off.TeamID)
lhp   = pm.read_i32(lpawn + off.CurrentHealth)
lpos  = pm.read_vec3(lpawn + off.Pos)
print(f"\n=== LOCAL PLAYER ===")
print(f"team={lteam} hp={lhp} pos={lpos}")

# Chunk[0]'da local controller'i bul
print("\n=== CHUNK LISTESI (tum chunklar) ===")
for ci in range(64):
    cp = pm.read_u64(chunk_array + ci * 0x8)
    if cp and 0x10000 < cp < 0x7FFFFFFFFFFF:
        print(f"  chunk[{ci}] = 0x{cp:X}")

print("\n=== TUM CHUNKLAR - ISIMLI OYUNCULAR (alive filtresi yok) ===")
for ci in range(64):
    cp = pm.read_u64(chunk_array + ci * 0x8)
    if not cp or cp > 0x7FFFFFFFFFFF or cp < 0x10000: continue
    for ei in range(512):
        ctrl = pm.read_u64(cp + ei * 0x8)
        if not ctrl or ctrl > 0x7FFFFFFFFFFF or ctrl < 0x10000: continue
        nr = pm.read_memory(ctrl + off.iszPlayerName, 32)
        if not nr: continue
        e = nr.find(b'\x00')
        name = nr[:e].decode(errors="ignore") if e!=-1 else ""
        if not name or len(name) < 2: continue
        alive = pm.read_i32(ctrl + off.IsAlive)
        team  = pm.read_i32(ctrl + off.TeamID)
        hp    = pm.read_i32(ctrl + off.Health)
        marker = " <-- LOCAL" if ctrl == lctrl else ""
        print(f"  [{ci}:{ei}] team={team} alive={alive} hp={hp} name='{name}'{marker}")

# Pawn okuma testi - local player
print(f"\n=== PAWN OKUMA TESTI ===")
ph = pm.read_u32(lctrl + off.PlayerPawn)
print(f"pawn_handle = 0x{ph:X}")
ci2 = (ph & 0x7FFF) >> 9
ei2 = ph & 0x1FF
print(f"  chunk_idx={ci2} ent_idx={ei2}")
ch2 = pm.read_u64(ges + 0x10 + 8*ci2)
print(f"  chunk ptr = 0x{ch2:X}")
if ch2:
    pawn = pm.read_u64(ch2 + 0x70*ei2)
    print(f"  pawn (0x70 stride) = 0x{pawn:X}")
    if pawn and pawn < 0x7FFFFFFFFFFF:
        phph = pm.read_i32(pawn + off.CurrentHealth)
        ppos = pm.read_vec3(pawn + off.Pos)
        print(f"  pawn hp={phph} pos={ppos}")
        screen = game.view.world_to_screen(ppos)
        print(f"  screen = {screen}")
