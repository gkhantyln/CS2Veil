"""Aimbot debug - ALT basili tutarken aim_pos ve mouse hareketi test et."""
import os,sys,time,struct,math,ctypes
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_BASE); sys.path.insert(0, _BASE)

from core.offsets import offsets; offsets.update()
from core.process_manager import process_mgr as pm; pm.attach("cs2.exe")
from core.game import game; game.init_address()
from core.offsets import offsets as off
from core.bone import BONEINDEX, BONE_JOINT_SIZE
from mods.aimbot import aim_config
from utils.kmbox import kmbox; kmbox.init_from_config("kmbox.json")

import win32con
user32 = ctypes.WinDLL("user32")

W,H=1360,768
game.view.set_screen_size(float(W),float(H))

print(f"Aim hotkey: {hex(aim_config.hotkey)} (Sol ALT={hex(win32con.VK_LMENU)})")
print(f"Aim FOV: {aim_config.fov}")
print(f"KmBox type: {kmbox.type}")
print("ALT'a bas ve bir dusmana bak - 10 saniye test...")

for _ in range(100):
    time.sleep(0.1)
    ak = bool(user32.GetAsyncKeyState(aim_config.hotkey) & 0x8000)
    alt_l = bool(user32.GetAsyncKeyState(win32con.VK_LMENU) & 0x8000)
    alt_r = bool(user32.GetAsyncKeyState(win32con.VK_RMENU) & 0x8000)
    
    if not (ak or alt_l or alt_r):
        continue
    
    print(f"  Tus algilandi: ak={ak} alt_l={alt_l} alt_r={alt_r}")
    
    game.update_matrix()
    game.update_entity_list_entry()
    ges=pm.read_u64(game.address.entity_list)
    base=game.address.entity_list_entry
    lc=pm.read_u64(game.address.local_controller)
    lp=pm.read_u64(game.address.local_pawn)
    
    if not all([ges,base,lc,lp]):
        print("  Entity list hazir degil"); continue
    
    lcam=pm.read_vec3(lp+off.vecLastClipCameraPos)
    lang=pm.read_vec2(lp+off.angEyeAngles)
    
    # En yakin entity bul
    aim_pos=None; max_d=float('inf')
    for ci in range(4):
        cp=pm.read_u64(base+ci*0x8)
        if not cp or cp>0x7FFFFFFFFFFF: continue
        for ei in range(512):
            ctrl=pm.read_u64(cp+ei*0x8)
            if not ctrl or ctrl>0x7FFFFFFFFFFF or ctrl<0x10000 or ctrl==lc: continue
            if pm.read_i32(ctrl+off.IsAlive)!=1: continue
            ph=pm.read_u32(ctrl+off.PlayerPawn)
            if not ph: continue
            c2=(ph&0x7FFF)>>9; e3=ph&0x1FF
            ch=pm.read_u64(ges+0x10+8*c2)
            if not ch: continue
            pawn=pm.read_u64(ch+0x70*e3)
            if not pawn or pawn>0x7FFFFFFFFFFF: continue
            hp=pm.read_i32(pawn+off.CurrentHealth)
            if hp<=0: continue
            
            # Head bone
            sc=pm.read_u64(pawn+off.GameSceneNode)
            if not sc: continue
            ba=pm.read_u64(sc+0x1E0)
            if not ba: continue
            rb=pm.read_memory(ba+BONEINDEX.neck_0*BONE_JOINT_SIZE,12)
            if not rb: continue
            nx,ny,nz=struct.unpack_from("<fff",rb)
            
            screen=game.view.world_to_screen((nx,ny,nz))
            if not screen: continue
            sx,sy=screen
            if not(0<sx<W and 0<sy<H): continue
            
            d=math.sqrt((sx-W/2)**2+(sy-H/2)**2)
            if d<max_d:
                max_d=d; aim_pos=(nx,ny,nz)
                print(f"  Hedef: screen=({sx:.0f},{sy:.0f}) dist={d:.0f} pos=({nx:.0f},{ny:.0f},{nz:.0f})")
    
    if aim_pos and max_d < aim_config.fov * W/90:
        sc=game.view.world_to_screen(aim_pos)
        if sc:
            tx=sc[0]-W/2; ty=sc[1]-H/2
            print(f"  Mouse hareket: tx={tx:.1f} ty={ty:.1f}")
            kmbox.move(tx/3, ty/3)  # /3 ile yumusatma
    elif aim_pos:
        print(f"  Hedef FOV disinda: dist={max_d:.0f} fov_px={aim_config.fov*W/90:.0f}")
    else:
        print("  Hedef bulunamadi")

print("Test bitti")
