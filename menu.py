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


def draw_menu():
    clear()

    cs2_ok     = check_cs2()
    offset_ok  = check_offsets()

    cs2_status    = f"{GREEN}Calisiyor{RESET}"    if cs2_ok    else f"{RED_GLOW}Bulunamadi{RESET}"
    offset_status = f"{GREEN}Mevcut{RESET}"       if offset_ok else f"{RED_GLOW}Eksik!{RESET}"

    print(f"{RED}{'='*52}{RESET}")
    print(f"{RED_GLOW}{BOLD}{'CS2VEIL':^52}{RESET}")
    print(f"{DIM}{'EXTERNAL  |  github@gkhantyln':^52}{RESET}")
    print(f"{RED}{'='*52}{RESET}")
    print()
    print(f"  {DIM}CS2        :{RESET}  {cs2_status}")
    print(f"  {DIM}Offset     :{RESET}  {offset_status}")
    print()
    print(f"{RED}{'-'*52}{RESET}")
    print()
    print(f"  {WHITE}{BOLD}[1]{RESET}  {WHITE}Baslat{RESET}")
    print(f"  {WHITE}{BOLD}[2]{RESET}  {DIM}Durumu Yenile{RESET}")
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
    os.system("mode con: cols=56 lines=28")

    while True:
        draw_menu()
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
            continue  # yenile

        elif choice == "0":
            clear()
            break


if __name__ == "__main__":
    main()
