"""
Config kayit/yukle sistemi - JSON formatinda.
Tum ayarlari config/ klasorune kaydeder.
"""
import json, os

CONFIG_DIR   = "config"
LAST_CFG_FILE = os.path.join(CONFIG_DIR, "_last.txt")


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def save_config(filename: str, menu_cfg, aim_cfg, trig_cfg, radar_cfg) -> bool:
    _ensure_dir()
    path = os.path.join(CONFIG_DIR, filename)
    if not path.endswith(".json"):
        path += ".json"

    data = {
        "visuals": {
            "show_box_esp":          menu_cfg.show_box_esp,
            "box_color":             menu_cfg.box_color,
            "box_type":              menu_cfg.box_type,
            "show_bone_esp":         menu_cfg.show_bone_esp,
            "bone_color":            menu_cfg.bone_color,
            "show_health_bar":       menu_cfg.show_health_bar,
            "health_bar_type":       menu_cfg.health_bar_type,
            "show_player_name":      menu_cfg.show_player_name,
            "player_name_pos":       menu_cfg.player_name_pos,
            "player_name_size":      menu_cfg.player_name_size,
            "show_distance":         menu_cfg.show_distance,
            "show_eye_ray":          menu_cfg.show_eye_ray,
            "eye_ray_color":         menu_cfg.eye_ray_color,
            "show_line_to_enemy":    menu_cfg.show_line_to_enemy,
            "line_to_enemy_color":   menu_cfg.line_to_enemy_color,
            "esp_fov_only":          menu_cfg.esp_fov_only,
            "crosshair_recoil":      menu_cfg.crosshair_recoil,
            "crosshair_sniper":      menu_cfg.crosshair_sniper,
            "crosshair_dynamic":     menu_cfg.crosshair_dynamic,
            "crosshair_snaplines":   menu_cfg.crosshair_snaplines,
            "crosshair_recoil_color":   menu_cfg.crosshair_recoil_color,
            "crosshair_sniper_color":   menu_cfg.crosshair_sniper_color,
            "crosshair_dynamic_color":  menu_cfg.crosshair_dynamic_color,
            "crosshair_dynamic_core":   menu_cfg.crosshair_dynamic_core,
            "crosshair_dynamic_size":   menu_cfg.crosshair_dynamic_size,
            "crosshair_dynamic_core_size": menu_cfg.crosshair_dynamic_core_size,
            "crosshair_snaplines_color":menu_cfg.crosshair_snaplines_color,
            "crosshair_arrows":         menu_cfg.crosshair_arrows,
            "crosshair_arrows_color":   menu_cfg.crosshair_arrows_color,
        },
        "settings": {
            "team_check":         menu_cfg.team_check,
            "no_flash":           menu_cfg.no_flash,
            "flash_max_alpha":    menu_cfg.flash_max_alpha,
        },
        "aimbot": {
            "enabled":            aim_cfg.enabled,
            "hotkey_index":       aim_cfg.hotkey_index,
            "fov":                aim_cfg.fov,
            "smooth":             aim_cfg.smooth,
            "fake_smooth":        aim_cfg.fake_smooth,
            "show_fov_circle":    aim_cfg.show_fov_circle,
            "fov_color":          aim_cfg.fov_color,
            "position":           aim_cfg.position,
            "position_pistol":    aim_cfg.position_pistol,
            "position_sniper":    aim_cfg.position_sniper,
            "auto_shot":          aim_cfg.auto_shot,
            "visible_check":      aim_cfg.visible_check,
            "ignore_on_shot":     aim_cfg.ignore_on_shot,
            "rcs_enabled":        aim_cfg.rcs_enabled,
            "rcs_scale":          aim_cfg.rcs_scale,
            "velocity_pred":      aim_cfg.velocity_pred,
        },
        "triggerbot": {
            "enabled":            trig_cfg.enabled,
            "hotkey_index":       trig_cfg.hotkey_index,
            "mode":               trig_cfg.mode,
            "delay_ms":           trig_cfg.delay_ms,
        },
        "radar": {},  # Kaldirildi
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Son kullanilan config'i kaydet
        with open(LAST_CFG_FILE, "w") as f:
            f.write(os.path.basename(path))
        return True
    except Exception as e:
        print(f"[ config ] Kayit hatasi: {e}")
        return False


def load_config(filename: str, menu_cfg, aim_cfg, trig_cfg, radar_cfg) -> bool:
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(path):
        print(f"[ config ] Dosya bulunamadi: {path}")
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ config ] Okuma hatasi: {e}")
        return False

    v = data.get("visuals", {})
    menu_cfg.show_box_esp        = v.get("show_box_esp",       menu_cfg.show_box_esp)
    menu_cfg.box_color           = v.get("box_color",          menu_cfg.box_color)
    menu_cfg.box_type            = v.get("box_type",           menu_cfg.box_type)
    menu_cfg.show_bone_esp       = v.get("show_bone_esp",      menu_cfg.show_bone_esp)
    menu_cfg.bone_color          = v.get("bone_color",         menu_cfg.bone_color)
    menu_cfg.show_health_bar     = v.get("show_health_bar",    menu_cfg.show_health_bar)
    menu_cfg.health_bar_type     = v.get("health_bar_type",    menu_cfg.health_bar_type)
    menu_cfg.show_player_name    = v.get("show_player_name",   menu_cfg.show_player_name)
    menu_cfg.player_name_pos     = v.get("player_name_pos",    menu_cfg.player_name_pos)
    menu_cfg.player_name_size    = v.get("player_name_size",   menu_cfg.player_name_size)
    menu_cfg.show_distance       = v.get("show_distance",      menu_cfg.show_distance)
    menu_cfg.show_eye_ray        = v.get("show_eye_ray",       menu_cfg.show_eye_ray)
    menu_cfg.eye_ray_color       = v.get("eye_ray_color",      menu_cfg.eye_ray_color)
    menu_cfg.show_line_to_enemy  = v.get("show_line_to_enemy", menu_cfg.show_line_to_enemy)
    menu_cfg.line_to_enemy_color = v.get("line_to_enemy_color",menu_cfg.line_to_enemy_color)
    menu_cfg.esp_fov_only        = v.get("esp_fov_only",       menu_cfg.esp_fov_only)
    menu_cfg.crosshair_recoil    = v.get("crosshair_recoil",   menu_cfg.crosshair_recoil)
    menu_cfg.crosshair_sniper    = v.get("crosshair_sniper",   menu_cfg.crosshair_sniper)
    menu_cfg.crosshair_dynamic   = v.get("crosshair_dynamic",  menu_cfg.crosshair_dynamic)
    menu_cfg.crosshair_snaplines = v.get("crosshair_snaplines",menu_cfg.crosshair_snaplines)
    menu_cfg.crosshair_recoil_color    = v.get("crosshair_recoil_color",    menu_cfg.crosshair_recoil_color)
    menu_cfg.crosshair_sniper_color    = v.get("crosshair_sniper_color",    menu_cfg.crosshair_sniper_color)
    menu_cfg.crosshair_dynamic_color   = v.get("crosshair_dynamic_color",   menu_cfg.crosshair_dynamic_color)
    menu_cfg.crosshair_dynamic_core    = v.get("crosshair_dynamic_core",    menu_cfg.crosshair_dynamic_core)
    menu_cfg.crosshair_dynamic_size    = v.get("crosshair_dynamic_size",    menu_cfg.crosshair_dynamic_size)
    menu_cfg.crosshair_dynamic_core_size = v.get("crosshair_dynamic_core_size", menu_cfg.crosshair_dynamic_core_size)
    menu_cfg.crosshair_snaplines_color = v.get("crosshair_snaplines_color", menu_cfg.crosshair_snaplines_color)
    menu_cfg.crosshair_arrows          = v.get("crosshair_arrows",          menu_cfg.crosshair_arrows)
    menu_cfg.crosshair_arrows_color    = v.get("crosshair_arrows_color",    menu_cfg.crosshair_arrows_color)

    s = data.get("settings", {})
    menu_cfg.team_check          = s.get("team_check",         menu_cfg.team_check)
    menu_cfg.no_flash            = s.get("no_flash",           menu_cfg.no_flash)
    menu_cfg.flash_max_alpha     = s.get("flash_max_alpha",    menu_cfg.flash_max_alpha)

    a = data.get("aimbot", {})
    aim_cfg.enabled              = a.get("enabled",            aim_cfg.enabled)
    aim_cfg.hotkey_index         = a.get("hotkey_index",       aim_cfg.hotkey_index)
    aim_cfg.fov                  = a.get("fov",                aim_cfg.fov)
    aim_cfg.smooth               = a.get("smooth",             aim_cfg.smooth)
    aim_cfg.fake_smooth          = a.get("fake_smooth",        aim_cfg.fake_smooth)
    aim_cfg.show_fov_circle      = a.get("show_fov_circle",    aim_cfg.show_fov_circle)
    aim_cfg.fov_color            = a.get("fov_color",          aim_cfg.fov_color)
    aim_cfg.position             = a.get("position",           aim_cfg.position)
    aim_cfg.position_pistol      = a.get("position_pistol",    aim_cfg.position_pistol)
    aim_cfg.position_sniper      = a.get("position_sniper",    aim_cfg.position_sniper)
    aim_cfg.auto_shot            = a.get("auto_shot",          aim_cfg.auto_shot)
    aim_cfg.visible_check        = a.get("visible_check",      aim_cfg.visible_check)
    aim_cfg.ignore_on_shot       = a.get("ignore_on_shot",     aim_cfg.ignore_on_shot)
    aim_cfg.rcs_enabled          = a.get("rcs_enabled",        aim_cfg.rcs_enabled)
    aim_cfg.rcs_scale            = a.get("rcs_scale",          aim_cfg.rcs_scale)
    aim_cfg.velocity_pred        = a.get("velocity_pred",      aim_cfg.velocity_pred)
    aim_cfg.apply_hotkey()

    t = data.get("triggerbot", {})
    trig_cfg.enabled             = t.get("enabled",            trig_cfg.enabled)
    trig_cfg.hotkey_index        = t.get("hotkey_index",       trig_cfg.hotkey_index)
    trig_cfg.mode                = t.get("mode",               trig_cfg.mode)
    trig_cfg.delay_ms            = t.get("delay_ms",           trig_cfg.delay_ms)
    trig_cfg.apply_hotkey()

    # Son kullanilan config'i guncelle
    with open(LAST_CFG_FILE, "w") as f:
        f.write(os.path.basename(path))

    print(f"[ config ] Yuklendi: {filename}")
    return True


def load_last_config(menu_cfg, aim_cfg, trig_cfg, radar_cfg) -> bool:
    """Program baslarken son kaydedilen config'i yukle."""
    if not os.path.exists(LAST_CFG_FILE):
        return False
    try:
        with open(LAST_CFG_FILE) as f:
            last = f.read().strip()
        if last:
            return load_config(last, menu_cfg, aim_cfg, trig_cfg, radar_cfg)
    except Exception:
        pass
    return False


def list_configs() -> list:
    """config/ klasoründeki tum .json dosyalarini listele."""
    _ensure_dir()
    return sorted([
        f for f in os.listdir(CONFIG_DIR)
        if f.endswith(".json") and not f.startswith("_")
    ])


def delete_config(filename: str) -> bool:
    path = os.path.join(CONFIG_DIR, filename)
    try:
        os.remove(path)
        return True
    except Exception:
        return False
