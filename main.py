import os
import random
import time

import cv2
import numpy as np
import pygame

from src.game_entities import *
from src.hand_tracker import HandTracker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")

UPGRADES = {
    "frost_plus": {"title": "Bang Lau Hon", "desc": "+0.8s freeze"},
    "shuriken_plus": {"title": "Them Dan", "desc": "+1 projectile moi skill"},
    "magnet_plus": {"title": "Hut Vat Pham", "desc": "Hut item tu xa hon"},
    "shield_plus": {"title": "Khien Day Hon", "desc": "+1.2s khi an khiên"},
}


def find_existing_file(directory, names):
    for name in names:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            return path
    return None


class MusicManager:
    def __init__(self, sounds_dir):
        self.sounds_dir = sounds_dir
        self.current_mode = None
        self.tracks = {
            "normal": self._find_track(["background.mp3", "background.mp3.mp3", "background.wav", "background.ogg"]),
            "boss": self._find_track(["boss_theme.wav", "boss_theme.mp3", "background.mp3"]),
            "danger": self._find_track(["danger_theme.wav", "danger_theme.mp3", "background.mp3"]),
            "victory": self._find_track(["victory_theme.wav", "victory_theme.mp3", "background.mp3"]),
        }

    def _find_track(self, names):
        return find_existing_file(self.sounds_dir, names)

    def play(self, mode, loops=-1, volume=0.4):
        if self.current_mode == mode:
            return
        track = self.tracks.get(mode)
        if not track:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
            self.current_mode = mode
        except pygame.error:
            return


def draw_glass_panel(frame, x1, y1, x2, y2, fill=(14, 20, 34), border=(90, 170, 220), alpha=0.48):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), fill, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), border, 1)


def draw_label(frame, text, x, y, color, scale=0.55, thickness=1):
    cv2.putText(frame, text, (x + 1, y + 1), cv2.FONT_HERSHEY_SIMPLEX, scale, (8, 10, 18), thickness + 2)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)


def draw_skill_chip(frame, x1, y1, x2, y2, title, desc, accent, active=False):
    fill = (22, 30, 48) if not active else (40, 54, 86)
    border = accent if active else (90, 110, 135)
    draw_glass_panel(frame, x1, y1, x2, y2, fill=fill, border=border, alpha=0.58)
    if active:
        cv2.rectangle(frame, (x1 + 6, y1 + 6), (x2 - 6, y2 - 6), accent, 1)
    draw_label(frame, title, x1 + 12, y1 + 24, accent, scale=0.53, thickness=2)
    draw_label(frame, desc, x1 + 12, y1 + 46, (232, 238, 245), scale=0.44, thickness=1)


class SeasonalBackdrop:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.seasons = ["spring", "summer", "autumn", "winter"]
        self.times = ["day", "sunset", "night"]
        self.season = "spring"
        self.time_mode = "day"
        self.particles = []
        self.clouds = []
        self._init_clouds()
        self._reseed_particles()

    def _init_clouds(self):
        self.clouds = []
        for idx in range(4):
            self.clouds.append(
                {
                    "x": random.randint(0, self.width),
                    "y": 50 + idx * 38,
                    "speed": 0.2 + idx * 0.05,
                    "size": 24 + idx * 6,
                }
            )

    def _reseed_particles(self):
        self.particles = []
        count = 26 if self.season != "winter" else 42
        for _ in range(count):
            self.particles.append(self._new_particle(random.uniform(0, self.height)))

    def _new_particle(self, y=None):
        if self.season == "winter":
            return {"x": random.uniform(0, self.width), "y": random.uniform(-20, self.height) if y is None else y,
                    "vx": random.uniform(-0.35, 0.35), "vy": random.uniform(0.8, 1.8), "r": random.randint(1, 3)}
        if self.season == "autumn":
            return {"x": random.uniform(0, self.width), "y": random.uniform(-20, self.height) if y is None else y,
                    "vx": random.uniform(-0.8, -0.15), "vy": random.uniform(0.45, 1.1), "r": random.randint(2, 4)}
        if self.season == "summer":
            return {"x": random.uniform(0, self.width), "y": random.uniform(-20, self.height) if y is None else y,
                    "vx": random.uniform(-0.15, 0.15), "vy": random.uniform(0.2, 0.6), "r": random.randint(1, 2)}
        return {"x": random.uniform(0, self.width), "y": random.uniform(-20, self.height) if y is None else y,
                "vx": random.uniform(-0.25, 0.25), "vy": random.uniform(0.3, 0.8), "r": random.randint(1, 3)}

    def set_state(self, level, boss_active):
        self.season = self.seasons[level % len(self.seasons)]
        self.time_mode = "night" if boss_active else self.times[(level // 2) % len(self.times)]
        if len(self.particles) == 0 or (self.season == "winter" and len(self.particles) < 35) or (self.season != "winter" and len(self.particles) > 35):
            self._reseed_particles()

    def _sky_tint(self):
        tints = {
            "day": (190, 120, 40),
            "sunset": (130, 90, 70),
            "night": (70, 40, 22),
        }
        return tints[self.time_mode]

    def _particle_color(self):
        if self.season == "winter":
            return (255, 250, 245)
        if self.season == "autumn":
            return (60, 170, 255)
        if self.season == "summer":
            return (140, 245, 255)
        return (170, 255, 180)

    def render(self, base_frame):
        frame = base_frame.copy()
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), self._sky_tint(), -1)
        cv2.addWeighted(overlay, 0.16 if self.time_mode == "day" else 0.26, frame, 1 - (0.16 if self.time_mode == "day" else 0.26), 0, frame)

        self._draw_sky_objects(frame)
        self._draw_hills(frame)
        self._draw_clouds(frame)
        self._draw_particles(frame)
        return frame

    def _draw_sky_objects(self, frame):
        if self.time_mode == "night":
            cv2.circle(frame, (680, 85), 26, (240, 240, 210), -1)
            for idx in range(12):
                sx = 60 + (idx * 57) % (self.width - 50)
                sy = 28 + (idx * 19) % 120
                cv2.circle(frame, (sx, sy), 1, (255, 255, 240), -1)
        else:
            sun_color = (120, 220, 255) if self.time_mode == "day" else (90, 170, 255)
            cv2.circle(frame, (680, 88), 30, sun_color, -1)
            cv2.circle(frame, (680, 88), 44, (170, 230, 255), 1)

    def _draw_hills(self, frame):
        hill_color_1 = (34, 70, 34) if self.season != "winter" else (170, 170, 170)
        hill_color_2 = (24, 50, 24) if self.season != "winter" else (140, 140, 140)
        pts_back = np.array([(0, 430), (110, 360), (250, 400), (410, 330), (590, 395), (800, 340), (800, 600), (0, 600)], np.int32)
        pts_front = np.array([(0, 500), (130, 430), (280, 470), (430, 410), (620, 470), (800, 420), (800, 600), (0, 600)], np.int32)
        cv2.fillConvexPoly(frame, pts_back, hill_color_1)
        cv2.fillConvexPoly(frame, pts_front, hill_color_2)

    def _draw_clouds(self, frame):
        for cloud in self.clouds:
            cloud["x"] -= cloud["speed"]
            if cloud["x"] < -90:
                cloud["x"] = self.width + 40
            cx = int(cloud["x"])
            cy = int(cloud["y"])
            color = (245, 245, 245) if self.time_mode != "night" else (110, 110, 130)
            cv2.circle(frame, (cx, cy), cloud["size"], color, -1)
            cv2.circle(frame, (cx + 20, cy + 2), int(cloud["size"] * 0.9), color, -1)
            cv2.circle(frame, (cx - 20, cy + 5), int(cloud["size"] * 0.7), color, -1)

    def _draw_particles(self, frame):
        color = self._particle_color()
        for particle in self.particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            if particle["x"] < -10:
                particle["x"] = self.width + 10
            if particle["x"] > self.width + 10:
                particle["x"] = -10
            if particle["y"] > self.height + 10:
                replacement = self._new_particle(-10)
                particle.update(replacement)
            center = (int(particle["x"]), int(particle["y"]))
            if self.season == "autumn":
                cv2.ellipse(frame, center, (particle["r"] + 1, particle["r"]), 30, 0, 360, color, -1)
            elif self.season == "summer":
                cv2.circle(frame, center, particle["r"], color, -1)
                cv2.circle(frame, center, particle["r"] + 2, (190, 255, 255), 1)
            elif self.season == "spring":
                cv2.circle(frame, center, particle["r"], color, -1)
            else:
                cv2.circle(frame, center, particle["r"], color, -1)


def init_audio():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        return True
    except pygame.error:
        return False


try:
    from tkinter import Tk

    root = Tk()
    SCREEN_W = root.winfo_screenwidth()
    SCREEN_H = root.winfo_screenheight()
    root.destroy()
except Exception:
    SCREEN_W, SCREEN_H = 1366, 768

GAME_W, GAME_H = 800, 600
init_audio()
MUSIC = MusicManager(SOUNDS_DIR)
MUSIC.play("normal")


def choose_by_hands(tracker, small_frame):
    hands = tracker.get_hands_data(small_frame, GAME_W, GAME_H, draw=True)
    left_hand = next((hand for hand in hands if hand["label"] == "Left"), None)
    right_hand = next((hand for hand in hands if hand["label"] == "Right"), None)
    fallback = hands[0]["fingers"] if len(hands) == 1 else None
    return hands, left_hand, right_hand, fallback


def show_menu_by_hand():
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    selected = "easy"
    confirmed = False
    confirm_hold_start = None

    cv2.namedWindow("Menu", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Menu", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))
        small = cv2.resize(frame, (GAME_W, GAME_H))

        hands, left_hand, right_hand, fallback = choose_by_hands(tracker, small)

        if left_hand:
            if left_hand["fingers"] == 1:
                selected = "easy"
            elif left_hand["fingers"] == 2:
                selected = "medium"
            elif left_hand["fingers"] == 3:
                selected = "hard"

        if right_hand and right_hand["fingers"] == 0:
            if confirm_hold_start is None:
                confirm_hold_start = time.time()
            elif time.time() - confirm_hold_start > 0.45:
                confirmed = True
                break
        else:
            confirm_hold_start = None

        if not left_hand and fallback is not None:
            if fallback == 1:
                selected = "easy"
            elif fallback == 2:
                selected = "medium"
            elif fallback == 3:
                selected = "hard"
            elif fallback == 0:
                confirmed = True
                break

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (SCREEN_W, SCREEN_H), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        scale = SCREEN_W / 800
        lines = [
            ("CHON DO KHO BANG TAY", 80, (0, 255, 255), 1.2),
            ("1 ngon tay trai: DE", 180, (255, 255, 255) if selected == "easy" else (150, 150, 150), 1.0),
            ("2 ngon tay trai: TRUNG BINH", 260, (255, 255, 255) if selected == "medium" else (150, 150, 150), 1.0),
            ("3 ngon tay trai: KHO", 340, (255, 255, 255) if selected == "hard" else (150, 150, 150), 1.0),
            ("TAY TRAI CHON, TAY PHAI NAM DE OK", 430, (0, 255, 0), 0.8),
            ("Neu chi thay 1 tay: 1-2-3 de chon, nam tay de vao", 470, (220, 220, 220), 0.6),
        ]
        for text, y, color, font_scale in lines:
            cv2.putText(frame, text, (int(SCREEN_W // 2 - 250 * scale), int(y * scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale * scale, color, 2)
        cv2.putText(frame, f"Dang chon: {selected.upper()}",
                    (int(SCREEN_W // 2 - 110 * scale), int(535 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8 * scale, (0, 255, 255), 2)
        if left_hand:
            cv2.putText(frame, f"Tay trai: {left_hand['fingers']} ngon", (25, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
        if right_hand:
            status = "NAM TAY" if right_hand["fingers"] == 0 else f"{right_hand['fingers']} ngon"
            cv2.putText(frame, f"Tay phai: {status}", (25, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Menu", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return selected if confirmed else None


def show_upgrade_menu(cap, tracker, upgrades, current_counts):
    confirm_hold_start = None
    selected_idx = 0
    MUSIC.play("victory", loops=-1, volume=0.45)
    while True:
        ret, frame = cap.read()
        if not ret:
            return None
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))
        small = cv2.resize(frame, (GAME_W, GAME_H))
        hands, left_hand, right_hand, fallback = choose_by_hands(tracker, small)

        if left_hand and 1 <= left_hand["fingers"] <= min(3, len(upgrades)):
            selected_idx = left_hand["fingers"] - 1
        elif fallback is not None and 1 <= fallback <= min(3, len(upgrades)):
            selected_idx = fallback - 1

        confirm_open = (right_hand and right_hand["fingers"] == 0) or fallback == 0
        if confirm_open:
            if confirm_hold_start is None:
                confirm_hold_start = time.time()
            elif time.time() - confirm_hold_start > 0.45:
                return upgrades[selected_idx]
        else:
            confirm_hold_start = None

        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (SCREEN_W, SCREEN_H), (8, 12, 30), -1)
        frame = cv2.addWeighted(overlay, 0.78, frame, 0.22, 0)
        cv2.putText(frame, "BOSS BIET MAT - CHON 1 NANG CAP", (90, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.15, (0, 255, 255), 3)
        for idx, key in enumerate(upgrades):
            y = 190 + idx * 125
            active = idx == selected_idx
            color = (0, 220, 255) if active else (140, 140, 160)
            cv2.rectangle(frame, (85, y - 40), (720, y + 40), (25, 35, 55), -1)
            cv2.rectangle(frame, (85, y - 40), (720, y + 40), color, 2)
            count = current_counts.get(key, 0)
            cv2.putText(frame, f"{idx + 1}. {UPGRADES[key]['title']}", (110, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            cv2.putText(frame, f"{UPGRADES[key]['desc']} | So lan: {count}", (110, y + 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (230, 230, 240), 2)
        cv2.putText(frame, "Tay trai 1-2-3 de chon, tay phai nam de nhan", (100, 560),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.68, (255, 255, 255), 2)
        cv2.imshow("Huyen thoai Ninja", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return None


def spawn_health_orb(pickups):
    pickups.append(HealthOrb(random.randint(GAME_W // 2 - 90, GAME_W // 2 + 90), -30, heal_amount=2))


def spawn_shield_orb(pickups):
    pickups.append(ShieldOrb(random.randint(GAME_W // 2 - 110, GAME_W // 2 + 110), -40, shield_time=2.0))


def apply_upgrade(ninja, key, counts):
    counts[key] = counts.get(key, 0) + 1
    if key == "frost_plus":
        ninja.freeze_bonus += 0.8
    elif key == "shuriken_plus":
        ninja.shuriken_bonus += 1
    elif key == "magnet_plus":
        ninja.item_magnet += 70
    elif key == "shield_plus":
        ninja.shield_bonus += 1.2


def combo_bonus_from_value(combo):
    tier = min(combo // 8, 4)
    damage_bonus = tier
    cooldown_scale = max(0.62, 1.0 - tier * 0.08)
    rare_drop_bonus = tier * 0.03
    return tier, damage_bonus, cooldown_scale, rare_drop_bonus


DIFFICULTY = {
    "easy": {"enemy_speed": 3, "enemy_hp": 1, "spawn_delay": 1.8, "boss_hp_mult": 0.8, "bullet_factor": 1.0},
    "medium": {"enemy_speed": 4, "enemy_hp": 2, "spawn_delay": 1.2, "boss_hp_mult": 1.0, "bullet_factor": 1.2},
    "hard": {"enemy_speed": 6, "enemy_hp": 3, "spawn_delay": 0.8, "boss_hp_mult": 1.5, "bullet_factor": 1.5},
}


def main():
    difficulty = show_menu_by_hand()
    if difficulty is None:
        return
    cfg = DIFFICULTY[difficulty]
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()

    bg = None
    if os.path.exists("assets/images/background.jpg"):
        bg = cv2.imread("assets/images/background.jpg")
        bg = cv2.resize(bg, (GAME_W, GAME_H))
    backdrop = SeasonalBackdrop(GAME_W, GAME_H)

    ninja = Ninja(100, GAME_H // 2)
    upgrade_counts = {}
    score = 0
    level = 0
    fingers = 0
    shurikens = []
    enemies = []
    bullets = []
    boss_lasers = []
    effects = []
    pickups = []
    boss = None
    game_over = False
    last_spawn = time.time()
    combo = 0
    last_combo_time = time.time()
    last_health_spawn = 0
    last_shield_spawn = 0
    victory_flash_until = 0
    MUSIC.play("normal")

    cv2.namedWindow("Huyen thoai Ninja", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Huyen thoai Ninja", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        small_frame = cv2.resize(frame, (GAME_W, GAME_H))

        if game_over:
            MUSIC.play("danger")
            display = cv2.resize(small_frame, (SCREEN_W, SCREEN_H))
            if bg is not None:
                bg_full = cv2.resize(bg, (SCREEN_W, SCREEN_H))
                display = cv2.addWeighted(bg_full, 0.5, display, 0.5, 0)
            scale = SCREEN_W / 800
            cv2.putText(display, "GAME OVER!", (int(SCREEN_W // 2 - 150 * scale), int(SCREEN_H // 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 2 * scale, (0, 0, 255), 5)
            cv2.putText(display, f"Diem: {score}  Level: {level + 1}",
                        (int(SCREEN_W // 2 - 150 * scale), int(SCREEN_H // 2 + 60 * scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1 * scale, (255, 255, 255), 2)
            cv2.putText(display, "Nhan 'R' choi lai | 'Q' thoat",
                        (int(SCREEN_W // 2 - 200 * scale), int(SCREEN_H // 2 + 120 * scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7 * scale, (255, 255, 0), 2)
            cv2.imshow("Huyen thoai Ninja", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("r"):
                ninja = Ninja(100, GAME_H // 2)
                upgrade_counts = {}
                score = 0
                level = 0
                fingers = 0
                shurikens.clear()
                enemies.clear()
                bullets.clear()
                boss_lasers.clear()
                effects.clear()
                pickups.clear()
                boss = None
                game_over = False
                combo = 0
                last_spawn = time.time()
                last_health_spawn = 0
                last_shield_spawn = 0
                victory_flash_until = 0
                MUSIC.play("normal")
            elif key == ord("q"):
                break
            continue

        found, px, py, fingers = tracker.get_player_action(small_frame, GAME_W, GAME_H)
        if found:
            ninja.update_position(px, py)
            ninja.defending = fingers == 0
            if fingers in [1, 2, 3, 5] and not ninja.defending:
                new_attacks = ninja.attack(fingers)
                shurikens.extend(new_attacks)
                if fingers == 5 and new_attacks:
                    effects.append(UltimateBurst(ninja.x, ninja.y, radius=120))

        tier, combo_damage_bonus, combo_cooldown_scale, rare_drop_bonus = combo_bonus_from_value(combo)
        ninja.set_combo_bonus(combo_damage_bonus, combo_cooldown_scale)

        now = time.time()
        if boss:
            MUSIC.play("boss", volume=0.46)
        elif ninja.hp <= 2:
            MUSIC.play("danger", volume=0.42)
        elif victory_flash_until > now:
            MUSIC.play("victory", volume=0.45)
        else:
            MUSIC.play("normal", volume=0.4)

        if boss is None and time.time() - last_spawn > cfg["spawn_delay"] / (level + 1):
            hp = cfg["enemy_hp"] + level // 3
            spd = cfg["enemy_speed"] + level // 5
            enemies.append(Enemy(GAME_W, random.randint(50, GAME_H - 50), hp, spd))
            last_spawn = time.time()

        if ninja.hp <= 2 and now - last_health_spawn > 10 and not any(isinstance(p, HealthOrb) for p in pickups):
            spawn_health_orb(pickups)
            last_health_spawn = now
        if now - last_shield_spawn > 14 and not any(isinstance(p, ShieldOrb) for p in pickups):
            spawn_shield_orb(pickups)
            last_shield_spawn = now

        if score > 0 and score % 20 == 0 and boss is None:
            boss_hp = int(55 * (level + 1) * cfg["boss_hp_mult"])
            boss = Boss(GAME_W - 120, GAME_H // 2, boss_hp, level + 1)
            enemies.clear()
            boss_lasers.clear()
            if boss_sound:
                boss_sound.play()

        for s in shurikens[:]:
            s.move()
            if isinstance(s, UltimateWave):
                for e in enemies[:]:
                    if id(e) not in s.already_hit and math.hypot(e.x - s.x, e.y - s.y) < s.radius:
                        e.hp -= s.damage
                        s.already_hit.add(id(e))
                if boss and id(boss) not in s.already_hit and math.hypot(boss.x - s.x, boss.y - s.y) < s.radius:
                    boss.hp -= s.damage
                    s.already_hit.add(id(boss))
                if s.is_finished():
                    shurikens.remove(s)
            elif s.x > GAME_W + 50 or s.y < -60 or s.y > GAME_H + 60:
                shurikens.remove(s)

        for laser in boss_lasers[:]:
            if not laser.is_active():
                boss_lasers.remove(laser)
                continue
            if laser.collides_with(ninja.x, ninja.y):
                if ninja.has_shield():
                    effects.append(IceBurst(ninja.x, ninja.y, radius=22))
                elif not ninja.defending:
                    ninja.hp -= 1
                    combo = 0
                    if hurt_sound:
                        hurt_sound.play()
                if ninja.hp <= 0:
                    game_over = True

        for b in bullets[:]:
            b.move()
            if b.x < -30 or b.y < -30 or b.y > GAME_H + 30:
                bullets.remove(b)
            elif abs(b.x - ninja.x) < 30 and abs(b.y - ninja.y) < 30:
                if ninja.has_shield():
                    effects.append(IceBurst(ninja.x, ninja.y, radius=18))
                elif not ninja.defending:
                    ninja.hp -= 1
                    combo = 0
                    if hurt_sound:
                        hurt_sound.play()
                bullets.remove(b)
                if ninja.hp <= 0:
                    game_over = True

        for e in enemies[:]:
            e.move()
            shot = e.shoot(level + 1, cfg["bullet_factor"])
            if shot:
                bullets.append(shot)
            for s in shurikens[:]:
                if isinstance(s, UltimateWave):
                    continue
                if abs(s.x - e.x) < 40 and abs(s.y - e.y) < 40:
                    e.hp -= s.damage
                    if isinstance(s, IceShard):
                        e.apply_freeze(s.freeze_time, s.slow_factor)
                        effects.append(IceBurst(e.x, e.y, radius=22))
                        if freeze_sound:
                            freeze_sound.play()
                    if s in shurikens:
                        shurikens.remove(s)
                    if hit_sound:
                        hit_sound.play()
                    break
            if e.hp <= 0:
                score += 1
                combo += 1
                last_combo_time = time.time()
                ninja.gain_ultimate(10)
                if random.random() < 0.06 + rare_drop_bonus:
                    spawn_health_orb(pickups) if random.random() < 0.5 else spawn_shield_orb(pickups)
                enemies.remove(e)
            elif e.x < -60:
                enemies.remove(e)

        if boss:
            boss.move()
            new_bullets, new_lasers, summons = boss.act()
            bullets.extend(new_bullets)
            boss_lasers.extend(new_lasers)
            for _ in range(summons):
                enemies.append(Enemy(GAME_W, random.randint(60, GAME_H - 60), cfg["enemy_hp"] + level // 2 + 1, cfg["enemy_speed"] + 1))
            for s in shurikens[:]:
                if isinstance(s, UltimateWave):
                    continue
                if abs(s.x - boss.x) < 85 and abs(s.y - boss.y) < 85:
                    boss.hp -= s.damage
                    if isinstance(s, IceShard):
                        boss.apply_freeze(max(0.8, s.freeze_time * 0.6), 0.55)
                        effects.append(IceBurst(boss.x, boss.y, radius=34))
                        if freeze_sound:
                            freeze_sound.play()
                    if s in shurikens:
                        shurikens.remove(s)
                    if hit_sound:
                        hit_sound.play()
                    break
            if boss.hp <= 0:
                score += 10
                level += 1
                combo += 5
                ninja.gain_ultimate(35)
                victory_flash_until = time.time() + 3.0
                chosen = show_upgrade_menu(cap, tracker, random.sample(list(UPGRADES.keys()), 3), upgrade_counts)
                if chosen:
                    apply_upgrade(ninja, chosen, upgrade_counts)
                boss = None
                boss_lasers.clear()
                last_spawn = time.time()

        for pickup in pickups[:]:
            pickup.update()
            if ninja.item_magnet > 0:
                dist = math.hypot(pickup.x - ninja.x, pickup.y - ninja.y)
                if dist < 90 + ninja.item_magnet:
                    pickup.x += (ninja.x - pickup.x) * 0.08
                    pickup.y += (ninja.y - pickup.y) * 0.08
            if pickup.y > GAME_H + 40:
                pickups.remove(pickup)
                continue
            if abs(pickup.x - ninja.x) < 36 and abs(pickup.y - ninja.y) < 36:
                if isinstance(pickup, HealthOrb):
                    ninja.heal(pickup.heal_amount)
                    effects.append(IceBurst(pickup.x, pickup.y, radius=20))
                elif isinstance(pickup, ShieldOrb):
                    ninja.activate_shield(pickup.shield_time)
                    effects.append(IceBurst(pickup.x, pickup.y, radius=24))
                pickups.remove(pickup)

        if time.time() - last_combo_time > 3:
            combo = 0

        if bg is not None:
            base_layer = cv2.addWeighted(bg, 0.82, small_frame, 0.18, 0)
        else:
            base_layer = np.full((GAME_H, GAME_W, 3), (22, 26, 34), dtype=np.uint8)
        backdrop.set_state(level, boss is not None)
        small_frame = backdrop.render(base_layer)
        if victory_flash_until > time.time():
            overlay = small_frame.copy()
            cv2.rectangle(overlay, (0, 0), (GAME_W, GAME_H), (130, 220, 255), -1)
            small_frame = cv2.addWeighted(overlay, 0.08, small_frame, 0.92, 0)

        ninja.draw(small_frame)
        for s in shurikens:
            s.draw(small_frame)
        for e in enemies:
            e.draw(small_frame)
        for b in bullets:
            b.draw(small_frame)
        for laser in boss_lasers:
            laser.draw(small_frame)
        if boss:
            boss.draw(small_frame)
        for pickup in pickups:
            pickup.draw(small_frame)
        for effect in effects[:]:
            effect.draw(small_frame)
            if not effect.update():
                effects.remove(effect)

        draw_glass_panel(small_frame, 12, 12, 184, 112, fill=(10, 18, 28), border=(82, 150, 210), alpha=0.42)
        draw_label(small_frame, f"HP {ninja.hp}/{ninja.max_hp}", 22, 36,
                   (90, 255, 130) if ninja.hp > 2 else (255, 90, 90), scale=0.62, thickness=2)
        draw_label(small_frame, f"Score {score}", 22, 62, (245, 245, 245), scale=0.54, thickness=2)
        draw_label(small_frame, f"ULT {int(ninja.ultimate_charge)}%", 22, 88, (255, 235, 150), scale=0.5, thickness=2)
        shield_text = f"Khien: {max(0.0, ninja.shield_until - time.time()):.1f}s" if ninja.has_shield() else "Khien: OFF"
        draw_label(small_frame, shield_text, 22, 108,
                   (0, 220, 255) if ninja.has_shield() else (180, 180, 180), scale=0.42, thickness=1)
        ult_ratio = ninja.ultimate_charge / ninja.ultimate_max
        cv2.rectangle(small_frame, (22, 94), (174, 102), (12, 14, 22), -1)
        cv2.rectangle(small_frame, (22, 94), (22 + int(152 * ult_ratio), 102), (255, 220, 95), -1)

        draw_glass_panel(small_frame, GAME_W - 154, 12, GAME_W - 12, 92, fill=(12, 18, 32), border=(110, 165, 220), alpha=0.42)
        draw_label(small_frame, f"Lv {level + 1}", GAME_W - 140, 36, (0, 255, 255), scale=0.62, thickness=2)
        draw_label(small_frame, f"Combo x{combo}", GAME_W - 140, 62, (255, 110, 220), scale=0.56, thickness=2)
        draw_label(small_frame, f"Tier {tier}", GAME_W - 140, 86, (255, 232, 125), scale=0.48, thickness=2)

        draw_glass_panel(small_frame, 12, GAME_H - 58, GAME_W - 12, GAME_H - 12, fill=(10, 15, 26), border=(90, 125, 170), alpha=0.38)
        draw_label(small_frame, f"{fingers} ngon", 24, GAME_H - 30, (210, 220, 228), scale=0.44, thickness=1)
        draw_skill_chip(small_frame, 96, GAME_H - 50, 180, GAME_H - 20, "1", "Nhanh", (235, 240, 245), active=fingers == 1)
        draw_skill_chip(small_frame, 188, GAME_H - 50, 272, GAME_H - 20, "2", "Rai", (200, 230, 255), active=fingers == 2)
        draw_skill_chip(small_frame, 280, GAME_H - 50, 392, GAME_H - 20, "3", "Bang", (255, 245, 170), active=fingers == 3)
        draw_skill_chip(small_frame, 404, GAME_H - 50, 566, GAME_H - 20, "5 NGON", "ULT", (255, 210, 95), active=fingers == 5 or ult_ratio >= 1.0)
        draw_label(small_frame, "Boss: fan | laser | summon", 584, GAME_H - 30, (200, 255, 255), scale=0.4, thickness=1)

        display_frame = cv2.resize(small_frame, (SCREEN_W, SCREEN_H))
        cv2.imshow("Huyen thoai Ninja", display_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
