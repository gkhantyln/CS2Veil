"""
Config save/load - mirrors C++ ConfigSaver.cpp.
"""
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ui.menu import MenuConfig


def save_config(filename: str, cfg, aim_cfg, trigger_cfg, radar_cfg):
    path = os.path.join(cfg.config_dir, filename)
    lines = [
        f"ShowBoneESP {int(cfg.show_bone_esp)}",
        f"ShowBoxESP {int(cfg.show_box_esp)}",
        f"ShowHealthBar {int(cfg.show_health_bar)}",
        f"ShowWeaponESP {int(cfg.show_weapon_esp)}",
        f"ShowDistance {int(cfg.show_distance)}",
        f"ShowEyeRay {int(cfg.show_eye_ray)}",
        f"ShowPlayerName {int(cfg.show_player_name)}",
        f"ShowLineToEnemy {int(cfg.show_line_to_enemy)}",
        f"BoxType {cfg.box_type}",
        f"HealthBarType {cfg.health_bar_type}",
        f"BoneColor {cfg.bone_color[0]} {cfg.bone_color[1]} {cfg.bone_color[2]} {cfg.bone_color[3]}",
        f"BoxColor {cfg.box_color[0]} {cfg.box_color[1]} {cfg.box_color[2]} {cfg.box_color[3]}",
        f"EyeRayColor {cfg.eye_ray_color[0]} {cfg.eye_ray_color[1]} {cfg.eye_ray_color[2]} {cfg.eye_ray_color[3]}",
        f"LineToEnemyColor {cfg.line_to_enemy_color[0]} {cfg.line_to_enemy_color[1]} {cfg.line_to_enemy_color[2]} {cfg.line_to_enemy_color[3]}",
        f"TeamCheck {int(cfg.team_check)}",
        f"AimBot {int(aim_cfg.enabled)}",
        f"AimBotHotKey {aim_cfg.hotkey_index}",
        f"AimFov {aim_cfg.fov}",
        f"Smooth {aim_cfg.smooth}",
        f"AimPosition {aim_cfg.position}",
        f"AimPositionPistol {aim_cfg.position_pistol}",
        f"AimPositionSniper {aim_cfg.position_sniper}",
        f"AimIgnoreOnShot {int(aim_cfg.ignore_on_shot)}",
        f"AutoShot {int(aim_cfg.auto_shot)}",
        f"VisibleCheck {int(aim_cfg.visible_check)}",
        f"ShowAimFovRange {int(aim_cfg.show_fov_circle)}",
        f"AimFovRangeColor {aim_cfg.fov_color[0]} {aim_cfg.fov_color[1]} {aim_cfg.fov_color[2]} {aim_cfg.fov_color[3]}",
        f"TriggerBot {int(trigger_cfg.enabled)}",
        f"TriggerHotKey {trigger_cfg.hotkey_index}",
        f"TriggerMode {trigger_cfg.mode}",
        f"TriggerDelay {trigger_cfg.delay_ms}",
        f"ShowRadar {int(radar_cfg.enabled)}",
        f"RadarType {radar_cfg.size_type}",
        f"RadarSize {radar_cfg.radar_size}",
        f"RadarLineLenght {radar_cfg.line_length}",
        f"RadarCircleSize {radar_cfg.circle_size}",
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def load_config(filename: str, cfg, aim_cfg, trigger_cfg, radar_cfg):
    path = os.path.join(cfg.config_dir, filename)
    if not os.path.exists(path):
        return

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            key = parts[0]
            val = parts[1:]

            def b(v): return bool(int(v[0]))
            def i(v): return int(v[0])
            def fl(v): return float(v[0])
            def color(v): return [float(x) for x in v[:4]]

            if key == "ShowBoneESP":       cfg.show_bone_esp       = b(val)
            elif key == "ShowBoxESP":      cfg.show_box_esp        = b(val)
            elif key == "ShowHealthBar":   cfg.show_health_bar     = b(val)
            elif key == "ShowWeaponESP":   cfg.show_weapon_esp     = b(val)
            elif key == "ShowDistance":    cfg.show_distance       = b(val)
            elif key == "ShowEyeRay":      cfg.show_eye_ray        = b(val)
            elif key == "ShowPlayerName":  cfg.show_player_name    = b(val)
            elif key == "ShowLineToEnemy": cfg.show_line_to_enemy  = b(val)
            elif key == "BoxType":         cfg.box_type            = i(val)
            elif key == "HealthBarType":   cfg.health_bar_type     = i(val)
            elif key == "BoneColor":       cfg.bone_color          = color(val)
            elif key == "BoxColor":        cfg.box_color           = color(val)
            elif key == "EyeRayColor":     cfg.eye_ray_color       = color(val)
            elif key == "LineToEnemyColor":cfg.line_to_enemy_color = color(val)
            elif key == "TeamCheck":       cfg.team_check          = b(val)
            elif key == "AimBot":          aim_cfg.enabled         = b(val)
            elif key == "AimBotHotKey":    aim_cfg.hotkey_index    = i(val); aim_cfg.apply_hotkey()
            elif key == "AimFov":          aim_cfg.fov             = fl(val)
            elif key == "Smooth":          aim_cfg.smooth          = fl(val)
            elif key == "AimPosition":     aim_cfg.position        = i(val)
            elif key == "AimPositionPistol":aim_cfg.position_pistol= i(val)
            elif key == "AimPositionSniper":aim_cfg.position_sniper= i(val)
            elif key == "AimIgnoreOnShot": aim_cfg.ignore_on_shot  = b(val)
            elif key == "AutoShot":        aim_cfg.auto_shot       = b(val)
            elif key == "VisibleCheck":    aim_cfg.visible_check   = b(val)
            elif key == "ShowAimFovRange": aim_cfg.show_fov_circle = b(val)
            elif key == "AimFovRangeColor":aim_cfg.fov_color       = color(val)
            elif key == "TriggerBot":      trigger_cfg.enabled     = b(val)
            elif key == "TriggerHotKey":   trigger_cfg.hotkey_index= i(val); trigger_cfg.apply_hotkey()
            elif key == "TriggerMode":     trigger_cfg.mode        = i(val)
            elif key == "TriggerDelay":    trigger_cfg.delay_ms    = i(val)
            elif key == "ShowRadar":       radar_cfg.enabled       = b(val)
            elif key == "RadarType":       radar_cfg.size_type     = i(val); radar_cfg.apply_size()
            elif key == "RadarSize":       radar_cfg.radar_size    = fl(val)
            elif key == "RadarLineLenght": radar_cfg.line_length   = i(val)
            elif key == "RadarCircleSize": radar_cfg.circle_size   = fl(val)
