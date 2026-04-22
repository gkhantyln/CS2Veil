"""
CS2Veil - Auto Updater
İki ayrı güncelleme kanalı:
  1. Offset güncelleme  — a2x/cs2-dumper (her CS2 güncellemesinde)
  2. Kod güncellemesi   — github@gkhantyln/CS2Veil (yeni özellikler)
"""
import os
import json
import hashlib
import shutil
import requests
from pathlib import Path

# ── Sabitler ──────────────────────────────────────────────────────────────────
# ── Sabitler ──────────────────────────────────────────────────────────────────
OFFSET_SOURCES = {
    "a2x": {
        "offsets":    "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json",
        "client_dll": "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json",
        "api":        "https://api.github.com/repos/a2x/cs2-dumper/commits?per_page=1&path=output/offsets.json",
        "label":      "a2x/cs2-dumper",
    },
    "sezzyaep": {
        "offsets":    "https://raw.githubusercontent.com/sezzyaep/CS2-OFFSETS/main/offsets.json",
        "client_dll": "https://raw.githubusercontent.com/sezzyaep/CS2-OFFSETS/main/client_dll.json",
        "api":        "https://api.github.com/repos/sezzyaep/CS2-OFFSETS/commits?per_page=1",
        "label":      "sezzyaep/CS2-OFFSETS",
    },
}

# Varsayılan kaynak (auto-update için)
OFFSET_URLS = {
    "offsets.json":    OFFSET_SOURCES["a2x"]["offsets"],
    "client.dll.json": OFFSET_SOURCES["a2x"]["client_dll"],
}

REPO_OWNER   = "gkhantyln"
REPO_NAME    = "CS2Veil"
REPO_BRANCH  = "main"
VERSION_FILE = "version.txt"
BACKUP_DIR   = "backup_old_version"

# Güncellenmemesi gereken dosyalar
SKIP_FILES = {
    ".gitignore", "imgui.ini", "kmbox.json",
    "offsets.json", "client.dll.json",  # bunlar ayrı kanaldan güncellenir
}
SKIP_DIRS = {".git", "__pycache__", "backup_old_version", ".kiro", "externalv2", "config", "xyazilim"}

TIMEOUT = 10

# ── Yardımcı ──────────────────────────────────────────────────────────────────
def _md5(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def _md5_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def _get(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r.content
    except Exception:
        return None

def _get_json(url: str) -> dict | None:
    data = _get(url)
    if data:
        try:
            return json.loads(data)
        except Exception:
            pass
    return None

# ── Offset kaynak bilgisi ─────────────────────────────────────────────────────
def get_source_info() -> dict:
    """Her iki kaynağın son güncelleme tarihini çeker."""
    result = {}
    for key, src in OFFSET_SOURCES.items():
        try:
            r = requests.get(src["api"], timeout=8)
            r.raise_for_status()
            commits = r.json()
            date_str = commits[0]["commit"]["author"]["date"] if commits else "?"
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                date_fmt = dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                date_fmt = date_str
            result[key] = {"date": date_fmt, "label": src["label"], "raw_date": date_str}
        except Exception:
            result[key] = {"date": "Baglanti hatasi", "label": src["label"], "raw_date": ""}
    return result


def download_offsets_from(source_key: str) -> tuple[int, int]:
    """Belirtilen kaynaktan offset dosyalarını indirir. Döner: (basarili, basarisiz)"""
    src = OFFSET_SOURCES.get(source_key)
    if not src:
        return 0, 1
    urls = {
        "offsets.json":    src["offsets"],
        "client.dll.json": src["client_dll"],
    }
    ok = 0; fail = 0
    for filename, url in urls.items():
        data = _get(url)
        if data is None:
            fail += 1; continue
        try:
            if os.path.exists(filename):
                shutil.copy2(filename, filename + ".bak")
            with open(filename, "wb") as f:
                f.write(data)
            ok += 1
        except Exception:
            fail += 1
    return ok, fail


# ── 1. Offset Güncelleme ──────────────────────────────────────────────────────
def check_offsets_update() -> dict:
    """
    a2x/cs2-dumper'dan offset dosyalarını kontrol eder.
    Döner: {"offsets.json": True/False, "client.dll.json": True/False}
    True = güncelleme var
    """
    result = {}
    for filename, url in OFFSET_URLS.items():
        remote = _get(url)
        if remote is None:
            result[filename] = False
            continue
        local_hash  = _md5(filename)
        remote_hash = _md5_bytes(remote)
        result[filename] = (local_hash != remote_hash)
    return result

def update_offsets(status: dict | None = None) -> tuple[int, int]:
    """
    Offset dosyalarını günceller.
    Döner: (güncellenen, başarısız)
    """
    if status is None:
        status = check_offsets_update()

    updated = 0
    failed  = 0
    for filename, needs_update in status.items():
        if not needs_update:
            continue
        url    = OFFSET_URLS[filename]
        remote = _get(url)
        if remote is None:
            failed += 1
            continue
        try:
            # Yedeği al
            if os.path.exists(filename):
                shutil.copy2(filename, filename + ".bak")
            with open(filename, "wb") as f:
                f.write(remote)
            updated += 1
        except Exception:
            failed += 1
    return updated, failed

# ── 2. Kod Güncellemesi ───────────────────────────────────────────────────────
def get_local_version() -> str:
    try:
        if Path(VERSION_FILE).exists():
            return Path(VERSION_FILE).read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return "0.0.0"

def get_remote_version() -> str | None:
    url  = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}/{VERSION_FILE}"
    data = _get(url)
    if data:
        return data.decode(errors="ignore").strip()
    return None

def get_remote_file_tree() -> list[dict] | None:
    """GitHub API ile repo dosya listesini al."""
    url  = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{REPO_BRANCH}?recursive=1"
    data = _get_json(url)
    if not data:
        return None
    files = []
    for item in data.get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item["path"]
        # Skip klasör ve dosyaları atla
        parts = Path(path).parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if Path(path).name in SKIP_FILES:
            continue
        files.append({
            "path": path,
            "url":  f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}/{path}",
        })
    return files

def _backup():
    """Mevcut dosyaları yedekle."""
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR, ignore_errors=True)
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != BACKUP_DIR]
        for fname in files:
            if fname in SKIP_FILES:
                continue
            src = os.path.join(root, fname)
            dst = os.path.join(BACKUP_DIR, os.path.relpath(src, "."))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass

def update_code(file_tree: list[dict] | None = None) -> tuple[int, int, int]:
    """
    Kod dosyalarını günceller.
    Döner: (güncellenen, değişmeyen, başarısız)
    """
    if file_tree is None:
        file_tree = get_remote_file_tree()
    if not file_tree:
        return 0, 0, 1

    _backup()

    updated  = 0
    skipped  = 0
    failed   = 0

    for item in file_tree:
        local_path = item["path"]
        remote     = _get(item["url"])
        if remote is None:
            failed += 1
            continue

        if os.path.exists(local_path) and _md5(local_path) == _md5_bytes(remote):
            skipped += 1
            continue

        try:
            os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(remote)
            updated += 1
        except Exception:
            failed += 1

    return updated, skipped, failed

# ── Ana kontrol fonksiyonu (menu.py'den çağrılır) ─────────────────────────────
def run_startup_check(print_fn=print) -> dict:
    """
    Program başlangıcında çalışır.
    Döner: {
        "offset_update": bool,   # offset güncellendi mi
        "code_update":   bool,   # yeni kod sürümü var mı
        "remote_version": str,
        "local_version":  str,
        "offset_status":  dict,
    }
    """
    result = {
        "offset_update":  False,
        "code_update":    False,
        "remote_version": None,
        "local_version":  get_local_version(),
        "offset_status":  {},
    }

    print_fn("[ update ] Guncelleme kontrol ediliyor...")

    # Offset kontrolü
    try:
        offset_status = check_offsets_update()
        result["offset_status"] = offset_status
        needs = [f for f, v in offset_status.items() if v]
        if needs:
            print_fn(f"[ update ] Offset guncelleniyor: {', '.join(needs)}")
            updated, failed = update_offsets(offset_status)
            result["offset_update"] = updated > 0
            if updated:
                print_fn(f"[ update ] {updated} offset dosyasi guncellendi.")
            if failed:
                print_fn(f"[ update ] {failed} dosya guncellenemedi.")
        else:
            print_fn("[ update ] Offsetler guncel.")
    except Exception as e:
        print_fn(f"[ update ] Offset kontrol hatasi: {e}")

    # Kod sürüm kontrolü
    try:
        remote_ver = get_remote_version()
        result["remote_version"] = remote_ver
        if remote_ver and remote_ver != result["local_version"]:
            result["code_update"] = True
            print_fn(f"[ update ] Yeni surum mevcut: {result['local_version']} -> {remote_ver}")
        else:
            print_fn(f"[ update ] Kod guncel ({result['local_version']}).")
    except Exception as e:
        print_fn(f"[ update ] Surum kontrol hatasi: {e}")

    return result
