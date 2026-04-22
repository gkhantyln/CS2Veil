"""
CS2Veil - Baslangic Menusu
"""
import os
import sys
import subprocess
import ctypes
from pathlib import Path

# Windows ANSI renk destegi
os.system("color")
os.system("chcp 65001 >nul 2>&1")

# ANSI renk kodlari
RED       = "\033[38;2;180;0;0m"
RED_LIGHT = "\033[38;2;220;50;50m"
RED_GLOW  = "\033[38;2;255;60;60m"
WHITE     = "\033[38;2;210;210;220m"
DIM       = "\033[38;2;80;80;90m"
YELLOW    = "\033[38;2;240;180;0m"
GREEN     = "\033[38;2;60;180;80m"
RESET     = "\033[0m"
BOLD      = "\033[1m"
BG_BLACK  = "\033[40m"


def clear():
    os.system("cls")


def check_cs2():
    kernel32 = ctypes.WinDLL("kernel32")
    snap = kernel32.CreateToolhelp32Snapshot(0x2, 0)
    if not snap:
        return False

    class PE(ctypes.Structure):
        _fields_ = [
            ("dwSize",             ctypes.c_uint32),
            ("cntUsage",           ctypes.c_uint32),
            ("th32ProcessID",      ctypes.c_uint32),
            ("th32DefaultHeapID",  ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID",       ctypes.c_uint32),
            ("cntThreads",         ctypes.c_uint32),
            ("th32ParentProcessID",ctypes.c_uint32),
            ("pcPriClassBase",     ctypes.c_long),
            ("dwFlags",            ctypes.c_uint32),
            ("szExeFile",          ctypes.c_char * 260),
        ]

    pe = PE()
    pe.dwSize = ctypes.sizeof(PE)
    found = False
    if kernel32.Process32First(snap, ctypes.byref(pe)):
        while True:
            if pe.szExeFile.decode(errors="ignore").lower() == "cs2.exe":
                found = True
                break
            if not kernel32.Process32Next(snap, ctypes.byref(pe)):
                break
    kernel32.CloseHandle(snap)
    return found


def check_offsets():
    return Path("offsets.json").exists() and Path("client.dll.json").exists()


def check_offset_freshness():
    """
    Başlangıçta offset kaynaklarının tarihlerini kontrol eder.
    Mevcut offsets.json'un tarihini kaynaklarla karşılaştırır.
    Daha güncel kaynak varsa kullanıcıya sorar.
    """
    try:
        from utils.updater import get_source_info, download_offsets_from
        import json, os, hashlib

        clear()
        print(f"\n  {DIM}Offset kaynaklari kontrol ediliyor...{RESET}\n")

        info = get_source_info()

        # En güncel kaynağı bul
        best_key = None
        best_date = ""
        for key, val in info.items():
            if val["raw_date"] > best_date:
                best_date = val["raw_date"]
                best_key = key

        if not best_key:
            return {}

        best = info[best_key]

        # Mevcut offsets.json'un hash'ini al
        current_hash = ""
        if os.path.exists("offsets.json"):
            with open("offsets.json", "rb") as f:
                current_hash = hashlib.md5(f.read()).hexdigest()

        # En güncel kaynaktan hash al
        import requests
        from utils.updater import OFFSET_SOURCES
        try:
            r = requests.get(OFFSET_SOURCES[best_key]["offsets"], timeout=8)
            remote_hash = hashlib.md5(r.content).hexdigest()
        except Exception:
            return {}

        if current_hash == remote_hash:
            print(f"  {GREEN}[OK]{RESET} Offsetler guncel ({best['label']} - {best['date']})")
            import time; time.sleep(1)
            return {"offset_ok": True}

        # Farklı — güncelleme var
        print(f"  {YELLOW}[!] Daha guncel offset mevcut:{RESET}")
        print()
        for key, val in info.items():
            marker = f"  {GREEN}← EN GUNCEL{RESET}" if key == best_key else ""
            print(f"      {WHITE}{val['label']}{RESET}  {DIM}{val['date']}{RESET}{marker}")
        print()
        print(f"  {YELLOW}Offsetleri guncellemek ister misiniz? (e/H): {RESET}", end="", flush=True)

        try:
            ans = input().strip().lower()
        except Exception:
            ans = ""

        if ans in ("e", "evet", "y", "yes"):
            print(f"\n  {DIM}{best['label']} kaynagindan indiriliyor...{RESET}")
            ok, fail = download_offsets_from(best_key)
            if ok == 2:
                print(f"  {GREEN}[OK] Offsetler guncellendi!{RESET}")
            else:
                print(f"  {YELLOW}[!] {ok} dosya guncellendi, {fail} basarisiz{RESET}")
            import time; time.sleep(1)
            return {"offset_updated": True, "source": best_key}
        else:
            print(f"  {DIM}Guncelleme atlandi.{RESET}")
            import time; time.sleep(1)
            return {"offset_skipped": True}

    except Exception as e:
        print(f"  {DIM}Offset kontrol hatasi: {e}{RESET}")
        import time; time.sleep(1)
        return {}


def run_offset_update():
    """Offset güncelleme — kaynak seçimi ile."""
    try:
        from utils.updater import get_source_info, download_offsets_from
        clear()
        print(f"\n  {DIM}Offset kaynaklari kontrol ediliyor...{RESET}\n")

        info = get_source_info()

        print(f"{RED}{'='*52}{RESET}")
        print(f"{WHITE}{BOLD}  Offset Guncelleme{RESET}")
        print(f"{RED}{'-'*52}{RESET}")
        print()

        sources = list(info.items())
        for i, (key, val) in enumerate(sources, 1):
            print(f"  {WHITE}{BOLD}[{i}]{RESET}  {val['label']}")
            print(f"       {DIM}Son guncelleme: {val['date']}{RESET}")
            print()

        print(f"  {WHITE}{BOLD}[0]{RESET}  {DIM}Iptal{RESET}")
        print()
        print(f"{RED}{'-'*52}{RESET}")
        print(f"\n  {DIM}Secim: {RESET}", end="", flush=True)

        try:
            choice = input().strip()
        except Exception:
            return

        if choice == "0" or not choice:
            return

        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(sources):
                return
        except ValueError:
            return

        source_key = sources[idx][0]
        source_label = sources[idx][1]["label"]

        print(f"\n  {DIM}{source_label} kaynagindan indiriliyor...{RESET}")
        ok, fail = download_offsets_from(source_key)

        if ok == 2:
            print(f"  {GREEN}[OK] Offsetler guncellendi ({source_label}){RESET}")
        elif ok > 0:
            print(f"  {YELLOW}[!] {ok} dosya guncellendi, {fail} basarisiz{RESET}")
        else:
            print(f"  {RED}[!!] Guncelleme basarisiz!{RESET}")

        input(f"\n  {DIM}Devam etmek icin Enter...{RESET}")

    except Exception as e:
        print(f"\n  {RED}Hata: {e}{RESET}")
        input(f"\n  {DIM}Devam etmek icin Enter...{RESET}")


def draw_menu(update_info=None):
    clear()

    cs2_ok     = check_cs2()
    offset_ok  = check_offsets()

    cs2_status    = f"{GREEN}Calisiyor{RESET}"    if cs2_ok    else f"{RED_GLOW}Bulunamadi{RESET}"
    offset_status = f"{GREEN}Mevcut{RESET}"       if offset_ok else f"{RED_GLOW}Eksik!{RESET}"

    # Güncelleme durumu
    update_line = ""
    if update_info:
        if update_info.get("offset_update"):
            update_line = f"  {GREEN}[✓] Offsetler guncellendi{RESET}\n"
        if update_info.get("code_update"):
            rv = update_info.get("remote_version", "?")
            update_line += f"  {YELLOW}[!] Yeni surum mevcut: {rv}{RESET}\n"

    print(f"{RED}{'='*52}{RESET}")
    print(f"{RED_GLOW}{BOLD}{'CS2VEIL':^52}{RESET}")
    print(f"{DIM}{'EXTERNAL  |  github@gkhantyln':^52}{RESET}")
    print(f"{RED}{'='*52}{RESET}")
    print()
    print(f"  {DIM}CS2        :{RESET}  {cs2_status}")
    print(f"  {DIM}Offset     :{RESET}  {offset_status}")
    if update_line:
        print(update_line, end="")
    print()
    print(f"{RED}{'-'*52}{RESET}")
    print()
    print(f"  {WHITE}{BOLD}[1]{RESET}  {WHITE}Baslat{RESET}")
    print(f"  {WHITE}{BOLD}[2]{RESET}  {DIM}Durumu Yenile{RESET}")
    print(f"  {WHITE}{BOLD}[3]{RESET}  {DIM}Guncelleme Kontrol{RESET}")
    print(f"  {WHITE}{BOLD}[4]{RESET}  {DIM}Offset Guncelle{RESET}")
    print(f"  {WHITE}{BOLD}[0]{RESET}  {DIM}Cikis{RESET}")
    print()
    print(f"{RED}{'-'*52}{RESET}")

    if not offset_ok:
        print(f"\n  {YELLOW}[!] Offset dosyalari eksik:{RESET}")
        print(f"  {DIM}https://github.com/a2x/cs2-dumper/tree/main/output{RESET}")

    if not cs2_ok:
        print(f"\n  {YELLOW}[!] CS2'yi once Pencereli Tam Ekran modunda acin.{RESET}")

    print()
    print(f"  {DIM}Secim: {RESET}", end="", flush=True)


def main():
    # Konsol boyutu
    os.system("mode con: cols=56 lines=32")

    # Başlangıçta offset tazelik kontrolü
    update_info = {}
    try:
        update_info = check_offset_freshness()
    except Exception:
        pass

    while True:
        draw_menu(update_info)
        try:
            choice = input().strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            clear()
            print(f"\n  {GREEN}Baslatiliyor...{RESET}\n")
            try:
                subprocess.Popen(
                    [sys.executable, "main.py"],
                    cwd=str(Path(__file__).parent)
                )
                print(f"  {GREEN}CS2Veil calisiyor.{RESET}")
                print(f"  {DIM}INSERT = Oyun ici menu{RESET}")
                print(f"\n  {DIM}Bu pencereyi kapatabilirsiniz.{RESET}\n")
            except Exception as e:
                print(f"  {RED_GLOW}Hata: {e}{RESET}\n")
            input(f"  {DIM}Devam etmek icin Enter...{RESET}")

        elif choice == "2":
            update_info = {}
            continue

        elif choice == "3":
            update_info = check_offset_freshness()

        elif choice == "4":
            run_offset_update()
            update_info = {}

        elif choice == "0":
            clear()
            break


if __name__ == "__main__":
    main()
