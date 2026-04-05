"""Head ve ankle bone screen pozisyonlarini goster."""
import os,sys,struct,time
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_BASE); sys.path.insert(0, _BASE)
from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off
from core.bone import BONEINDEX, BONE_JOINT_SIZE

W,H=1360,768
game.view.set_screen_size(float(W),float(H))

for _ in range(3):
    game.update_matrix()
    game.update_entity_list_entry()
    ges=pm.read_u64(game.address.entity_list)
    base=game.address.entity_list_entry
    lc=pm.read_u64(game.address.local_controller)

    for ci in range(2):
        cp=pm.read_u64(base+ci*0x8)
        if not cp or cp>0x7FFFFFFFFFFF: continue
        for ei in range(512):
            ctrl=pm.read_u64(cp+ei*0x8)
            if not ctrl or ctrl>0x7FFFFFFFFFFF or ctrl<0x10000 or ctrl==lc: continue
            if pm.read_i32(ctrl+off.IsAlive)!=1: continue
            nr=pm.read_memory(ctrl+off.iszPlayerName,32)
            if not nr: continue
            e=nr.find(b'\x00'); name=nr[:e].decode(errors="ignore") if e!=-1 else ""
            if not name: continue
            ph=pm.read_u32(ctrl+off.PlayerPawn)
            if not ph: continue
            c2=(ph&0x7FFF)>>9; e3=ph&0x1FF
            ch=pm.read_u64(ges+0x10+8*c2)
            if not ch: continue
            pawn=pm.read_u64(ch+0x70*e3)
            if not pawn or pawn>0x7FFFFFFFFFFF: continue
            hp=pm.read_i32(pawn+off.CurrentHealth)
            if hp<=0: continue

            sc=pm.read_u64(pawn+off.GameSceneNode)
            if not sc: continue
            ba=pm.read_u64(sc+off.BoneArray)
            if not ba: continue
            raw=pm.read_memory(ba,30*BONE_JOINT_SIZE)
            if not raw: continue

            pos=pm.read_vec3(pawn+off.Pos)
            foot_s=game.view.world_to_screen(pos)

            # Head (6), Neck (5), Ankle_L (24), Ankle_R (27)
            bones_to_check = {
                "head(6)": BONEINDEX.head,
                "neck(5)": BONEINDEX.neck_0,
                "ankle_L(24)": 24,
                "ankle_R(27)": 27,
                "pelvis(0)": 0,
            }
            print(f"\n{name} HP={hp}")
            print(f"  foot(pos) screen: {foot_s}")
            for bname, bidx in bones_to_check.items():
                o=bidx*BONE_JOINT_SIZE
                if o+12>len(raw): continue
                x,y,z=struct.unpack_from("<fff",raw,o)
                s=game.view.world_to_screen((x,y,z))
                in_screen = "IN" if s and 0<s[0]<W and 0<s[1]<H else "OUT"
                print(f"  {bname}: pos=({x:.0f},{y:.0f},{z:.0f}) screen={s} {in_screen}")
    time.sleep(1)
    print("---")
