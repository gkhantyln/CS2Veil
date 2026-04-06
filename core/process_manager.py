"""
Process Manager - ReadProcessMemory backend.
Replaces DMA/VMMDLL with standard Windows API.
Works on the same PC as CS2 (no hardware required).
"""
import ctypes
import ctypes.wintypes as wt
import struct
import time
from typing import Optional

# Windows API
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi    = ctypes.WinDLL("psapi",    use_last_error=True)

PROCESS_ALL_ACCESS      = 0x1F0FFF
PROCESS_VM_READ         = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
TH32CS_SNAPPROCESS      = 0x00000002

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize",              wt.DWORD),
        ("cntUsage",            wt.DWORD),
        ("th32ProcessID",       wt.DWORD),
        ("th32DefaultHeapID",   ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID",        wt.DWORD),
        ("cntThreads",          wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase",      ctypes.c_long),
        ("dwFlags",             wt.DWORD),
        ("szExeFile",           ctypes.c_char * 260),
    ]

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize",        wt.DWORD),
        ("th32ModuleID",  wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("GlblcntUsage",  wt.DWORD),
        ("ProccntUsage",  wt.DWORD),
        ("modBaseAddr",   ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize",   wt.DWORD),
        ("hModule",       wt.HMODULE),
        ("szModule",      ctypes.c_char * 256),
        ("szExePath",     ctypes.c_char * 260),
    ]

TH32CS_SNAPMODULE   = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010


class ProcessManager:
    def __init__(self):
        self._handle: Optional[wt.HANDLE] = None
        self.pid: int = 0
        # Pre-allocated reusable buffers — her read_memory çağrısında yeni allocate etme
        self._buf_8    = (ctypes.c_char * 8)()
        self._buf_64   = (ctypes.c_char * 64)()
        self._buf_4096 = (ctypes.c_char * 0x4000)()
        self._bytes_read = ctypes.c_size_t(0)
        self._write_buf_4 = ctypes.create_string_buffer(4)
        self._write_buf_8 = ctypes.create_string_buffer(8)

    # ------------------------------------------------------------------ attach
    def attach(self, process_name: str = "cs2.exe") -> bool:
        self.pid = self._find_pid(process_name)
        if not self.pid:
            print(f"[ error ] Process '{process_name}' not found. Is CS2 running?")
            return False

        self._handle = kernel32.OpenProcess(
            PROCESS_ALL_ACCESS, False, self.pid
        )
        if not self._handle:
            # Try with less permissions
            self._handle = kernel32.OpenProcess(
                PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, self.pid
            )
        if not self._handle:
            err = ctypes.get_last_error()
            print(f"[ error ] OpenProcess failed (err={err}). Try running as Administrator.")
            return False

        print(f"[ info ] Attached to {process_name} PID={self.pid}")
        return True

    def _find_pid(self, name: str) -> int:
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == wt.HANDLE(-1).value:
            return 0
        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        try:
            if kernel32.Process32First(snap, ctypes.byref(entry)):
                while True:
                    if entry.szExeFile.decode(errors="ignore").lower() == name.lower():
                        return entry.th32ProcessID
                    if not kernel32.Process32Next(snap, ctypes.byref(entry)):
                        break
        finally:
            kernel32.CloseHandle(snap)
        return 0

    # ------------------------------------------------------------------ modules
    def get_module_base(self, module_name: str) -> int:
        snap = kernel32.CreateToolhelp32Snapshot(
            TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid
        )
        if snap == wt.HANDLE(-1).value:
            return 0
        entry = MODULEENTRY32()
        entry.dwSize = ctypes.sizeof(MODULEENTRY32)
        try:
            if kernel32.Module32First(snap, ctypes.byref(entry)):
                while True:
                    if entry.szModule.decode(errors="ignore").lower() == module_name.lower():
                        return ctypes.cast(entry.modBaseAddr, ctypes.c_void_p).value or 0
                    if not kernel32.Module32Next(snap, ctypes.byref(entry)):
                        break
        finally:
            kernel32.CloseHandle(snap)
        return 0

    # ------------------------------------------------------------------ read
    def read_memory(self, address: int, size: int) -> Optional[bytes]:
        if not self._handle or not address:
            return None
        # Pre-allocated buffer'ları kullan — sık kullanılan boyutlar için allocation yok
        if size == 8:
            buf = self._buf_8
        elif size == 64:
            buf = self._buf_64
        elif size == 0x4000:
            buf = self._buf_4096
        else:
            buf = (ctypes.c_char * size)()
        ok = kernel32.ReadProcessMemory(
            self._handle, ctypes.c_void_p(address),
            buf, size, ctypes.byref(self._bytes_read)
        )
        return bytes(buf[:self._bytes_read.value]) if ok and self._bytes_read.value > 0 else None

    def read_pawn_block(self, pawn: int) -> Optional[bytes]:
        """Pawn'ın tüm netvars'ını tek ReadProcessMemory ile oku (16KB)."""
        return self.read_memory(pawn, 0x4000)

    def read_u8(self, addr: int) -> int:
        d = self.read_memory(addr, 1)
        return struct.unpack_from("<B", d)[0] if d and len(d) >= 1 else 0

    def read_u32(self, addr: int) -> int:
        d = self.read_memory(addr, 4)
        return struct.unpack_from("<I", d)[0] if d and len(d) >= 4 else 0

    def read_i32(self, addr: int) -> int:
        d = self.read_memory(addr, 4)
        return struct.unpack_from("<i", d)[0] if d and len(d) >= 4 else 0

    def read_u64(self, addr: int) -> int:
        d = self.read_memory(addr, 8)
        return struct.unpack_from("<Q", d)[0] if d and len(d) >= 8 else 0

    def read_float(self, addr: int) -> float:
        d = self.read_memory(addr, 4)
        return struct.unpack_from("<f", d)[0] if d and len(d) >= 4 else 0.0

    def read_vec2(self, addr: int):
        d = self.read_memory(addr, 8)
        return struct.unpack_from("<ff", d) if d and len(d) >= 8 else (0.0, 0.0)

    def read_vec3(self, addr: int):
        d = self.read_memory(addr, 12)
        return struct.unpack_from("<fff", d) if d and len(d) >= 12 else (0.0, 0.0, 0.0)

    def read_string(self, addr: int, max_len: int = 260) -> str:
        d = self.read_memory(addr, max_len)
        if not d:
            return ""
        end = d.find(b'\x00')
        return d[:end].decode(errors="ignore") if end != -1 else d.decode(errors="ignore")

    # ------------------------------------------------------------------ write
    def write_memory(self, address: int, data: bytes) -> bool:
        if not self._handle or not address:
            return False
        buf      = (ctypes.c_char * len(data))(*data)
        written  = ctypes.c_size_t(0)
        return bool(kernel32.WriteProcessMemory(
            self._handle, ctypes.c_void_p(address),
            buf, len(data), ctypes.byref(written)
        ))

    def write_u32(self, addr: int, value: int) -> bool:
        return self.write_memory(addr, struct.pack("<I", value))

    def write_vec2(self, addr: int, x: float, y: float) -> bool:
        return self.write_memory(addr, struct.pack("<ff", x, y))
    # ------------------------------------------------------------------ pointer chain
    def trace_address(self, base: int, offsets: list) -> int:
        if not offsets:
            return base
        addr = self.read_u64(base)
        if not addr:
            return 0
        for off in offsets[:-1]:
            addr = self.read_u64(addr + off)
            if not addr:
                return 0
        return addr + offsets[-1]

    # ------------------------------------------------------------------ scatter (emulated)
    # ReadProcessMemory doesn't have scatter, but we batch reads efficiently
    def create_scatter_handle(self):
        return []  # list of (address, size, buffer_ref)

    def scatter_prepare(self, handle: list, address: int, size: int):
        buf = bytearray(size)
        handle.append((address, size, buf))
        return buf

    def scatter_execute(self, handle: list):
        for address, size, buf in handle:
            data = self.read_memory(address, size)
            if data:
                buf[:len(data)] = data

    # ------------------------------------------------------------------ keys
    def init_keystates(self):
        pass  # GetAsyncKeyState needs no init

    def is_key_down(self, vk: int) -> bool:
        user32 = ctypes.WinDLL("user32")
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)


# Singleton
process_mgr = ProcessManager()
