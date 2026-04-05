"""
ImGui menu - Turkce arayuz.
Not: Turkce karakterler sistem fontuna baglidir.
"""
import imgui
import win32con
from core.bone import BONEINDEX
from mods.aimbot import aim_config, HOTKEY_LIST as AIM_HOTKEYS, HOTKEY_NAMES as AIM_HOTKEY_NAMES
from mods.triggerbot import trigger_config, HOTKEY_LIST as TRIG_HOTKEYS, HOTKEY_NAMES as TRIG_HOTKEY_NAMES
from mods.radar import radar_config
from utils.maps_data import map_state

# Turkce karakter tablosu - font destekliyorsa gercek, desteklemiyorsa ASCII fallback
def _t(tr_text, fallback=None):
    """Turkce metin - font destekliyorsa Turkce, yoksa fallback."""
    return tr_text  # font dogru yuklendiyse calisir


class MenuConfig:
    def __init__(self):
        self.config_dir         = "config"
        self.show_menu          = False  # INSERT ile ac
        self.show_box_esp       = True
        self.show_bone_esp      = False
        self.show_health_bar    = True
        self.show_weapon_esp    = False
        self.show_distance      = False
        self.show_eye_ray       = False
        self.show_player_name   = True
        self.player_name_pos    = 0      # 0=Ust, 1=Alt
        self.player_name_size   = 13     # Yazi boyutu (px)
        self.show_line_to_enemy = False
        self.box_type           = 0
        self.health_bar_type    = 0
        self.bone_color         = [1.0, 1.0, 1.0, 1.0]
        self.box_color          = [1.0, 1.0, 1.0, 1.0]
        self.eye_ray_color      = [1.0, 0.0, 0.0, 1.0]
        self.line_to_enemy_color= [1.0, 1.0, 1.0, 0.86]
        self.team_check         = True
        self.shoot              = False
        self.esp_fov_only       = True   # Sadece FOV icindekiler
        self.no_flash           = False  # No Flash
        self.flash_max_alpha    = 180    # 0=tam flash, 255=hic flash yok


menu_config = MenuConfig()
_config_name_buf = [""]
_selected_config = [-1]


def render_menu():
    import os

    imgui.begin("CS2 / DMA Hile", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)
    imgui.begin_tab_bar("sekmeler")

    # ── Gorsel ──────────────────────────────────────────────────────────
    if imgui.begin_tab_item("Gorsel")[0]:
        _, menu_config.show_box_esp = imgui.checkbox("Kutu ESP", menu_config.show_box_esp)
        imgui.same_line()
        changed, val = imgui.color_edit4("Kutu Rengi##box", *menu_config.box_color,
                                          flags=imgui.COLOR_EDIT_NO_INPUTS)
        if changed: menu_config.box_color = list(val)

        _, menu_config.box_type = imgui.combo("Kutu Tipi", menu_config.box_type,
                                               ["Normal", "Ince"])

        _, menu_config.show_bone_esp = imgui.checkbox("Iskelet ESP", menu_config.show_bone_esp)
        imgui.same_line()
        changed, val = imgui.color_edit4("Iskelet Rengi##bone", *menu_config.bone_color,
                                          flags=imgui.COLOR_EDIT_NO_INPUTS)
        if changed: menu_config.bone_color = list(val)

        _, menu_config.show_eye_ray = imgui.checkbox("Bakis Cizgisi", menu_config.show_eye_ray)
        imgui.same_line()
        changed, val = imgui.color_edit4("Bakis Rengi##eye", *menu_config.eye_ray_color,
                                          flags=imgui.COLOR_EDIT_NO_INPUTS)
        if changed: menu_config.eye_ray_color = list(val)

        _, menu_config.show_health_bar = imgui.checkbox("Can Bari", menu_config.show_health_bar)
        _, menu_config.health_bar_type = imgui.combo("Can Bari Konumu",
                                                      menu_config.health_bar_type,
                                                      ["Sol", "Ust"])

        _, menu_config.show_weapon_esp  = imgui.checkbox("Silah Adi", menu_config.show_weapon_esp)
        _, menu_config.show_distance    = imgui.checkbox("Mesafe", menu_config.show_distance)
        _, menu_config.show_player_name = imgui.checkbox("Oyuncu Adi", menu_config.show_player_name)

        _, menu_config.show_line_to_enemy = imgui.checkbox("Dusmana Cizgi",
                                                            menu_config.show_line_to_enemy)
        imgui.same_line()
        changed, val = imgui.color_edit4("Cizgi Rengi##line", *menu_config.line_to_enemy_color,
                                          flags=imgui.COLOR_EDIT_NO_INPUTS)
        if changed: menu_config.line_to_enemy_color = list(val)

        imgui.end_tab_item()

    # ── Nishan Botu ─────────────────────────────────────────────────────
    if imgui.begin_tab_item("Nishan Botu")[0]:
        _, aim_config.enabled = imgui.checkbox("Aktif##aim", aim_config.enabled)

        changed, aim_config.hotkey_index = imgui.combo(
            "Tus##aim", aim_config.hotkey_index, AIM_HOTKEY_NAMES)
        if changed:
            aim_config.apply_hotkey()

        _, aim_config.fov = imgui.slider_float("FOV", aim_config.fov, 0.1, 89.0, "%.1f")

        _, aim_config.show_fov_circle = imgui.checkbox("FOV Cemberi", aim_config.show_fov_circle)
        imgui.same_line()
        changed, val = imgui.color_edit4("FOV Rengi##fov", *aim_config.fov_color,
                                          flags=imgui.COLOR_EDIT_NO_INPUTS)
        if changed: aim_config.fov_color = list(val)

        _, aim_config.smooth = imgui.slider_float("Yumusatma", aim_config.smooth,
                                                   0.0, 0.9, "%.1f")

        _, aim_config.position = imgui.combo(
            "Hedef (Normal)", aim_config.position, ["Kafa", "Boyun", "Govde"])

        _, aim_config.position_pistol = imgui.combo(
            "Hedef (Tabanca)", aim_config.position_pistol, ["Kafa", "Boyun", "Govde"])

        _, aim_config.position_sniper = imgui.combo(
            "Hedef (Keskin)", aim_config.position_sniper, ["Kafa", "Boyun", "Govde"])

        _, aim_config.auto_shot      = imgui.checkbox("Oto Ates", aim_config.auto_shot)
        imgui.same_line()
        _, aim_config.visible_check  = imgui.checkbox("Gorunurluk", aim_config.visible_check)
        _, aim_config.ignore_on_shot = imgui.checkbox("Ates Ederken Dur",
                                                       aim_config.ignore_on_shot)

        imgui.separator()
        imgui.text_colored("Aktif Tus: " + AIM_HOTKEY_NAMES[aim_config.hotkey_index],
                           0.4, 1.0, 0.4, 1.0)
        imgui.end_tab_item()

    # ── Radar ────────────────────────────────────────────────────────────
    if imgui.begin_tab_item("Radar")[0]:
        _, radar_config.enabled = imgui.checkbox("Radari Goster", radar_config.enabled)
        changed, radar_config.size_type = imgui.combo("Radar Boyutu",
                                                       radar_config.size_type,
                                                       ["Kucuk", "Buyuk"])
        if changed:
            radar_config.apply_size()
        imgui.end_tab_item()

    # ── Tetik Botu ───────────────────────────────────────────────────────
    if imgui.begin_tab_item("Tetik Botu")[0]:
        _, trigger_config.enabled = imgui.checkbox("Aktif##trig", trigger_config.enabled)

        changed, trigger_config.hotkey_index = imgui.combo(
            "Tus##trig", trigger_config.hotkey_index, TRIG_HOTKEY_NAMES)
        if changed:
            trigger_config.apply_hotkey()

        _, trigger_config.mode = imgui.combo("Mod", trigger_config.mode,
                                              ["Tusa Basinca", "Her Zaman"])
        _, trigger_config.delay_ms = imgui.slider_int("Gecikme (ms)",
                                                       trigger_config.delay_ms, 0, 250)

        imgui.separator()
        imgui.text_colored("Aktif Tus: " + TRIG_HOTKEY_NAMES[trigger_config.hotkey_index],
                           0.4, 1.0, 0.4, 1.0)
        imgui.end_tab_item()

    # ── Ayarlar ──────────────────────────────────────────────────────────
    if imgui.begin_tab_item("Ayarlar")[0]:
        _, menu_config.team_check = imgui.checkbox("Takim Kontrolu", menu_config.team_check)
        imgui.separator()
        imgui.text("INSERT = Menu ac/kapat")
        imgui.spacing()
        if imgui.button("Programi Kapat"):
            import sys
            sys.exit(0)
        imgui.end_tab_item()

    # ── Konfig ───────────────────────────────────────────────────────────
    if imgui.begin_tab_item("Konfig")[0]:
        _render_config_tab()
        imgui.end_tab_item()

    imgui.separator()
    imgui.end_tab_bar()
    imgui.end()


def _render_config_tab():
    import os
    from utils.config_saver import save_config, load_config

    changed, _config_name_buf[0] = imgui.input_text("Konfig Adi", _config_name_buf[0], 128)
    if imgui.button("Olustur") and _config_name_buf[0]:
        save_config(_config_name_buf[0] + ".config",
                    menu_config, aim_config, trigger_config, radar_config)

    imgui.separator()

    cfg_dir = menu_config.config_dir
    files = []
    if os.path.isdir(cfg_dir):
        files = [f for f in os.listdir(cfg_dir) if f.endswith(".config")]

    for i, fname in enumerate(files):
        clicked, _ = imgui.selectable(fname, _selected_config[0] == i)
        if clicked:
            _selected_config[0] = i

    sel = _selected_config[0]
    if imgui.button("Yukle") and 0 <= sel < len(files):
        load_config(files[sel], menu_config, aim_config, trigger_config, radar_config)
    imgui.same_line()
    if imgui.button("Kaydet") and 0 <= sel < len(files):
        save_config(files[sel], menu_config, aim_config, trigger_config, radar_config)
    imgui.same_line()
    if imgui.button("Sil") and 0 <= sel < len(files):
        os.remove(os.path.join(cfg_dir, files[sel]))
        _selected_config[0] = -1
