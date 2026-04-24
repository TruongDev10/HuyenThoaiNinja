import math
import os
import random
import time

import cv2
import cvzone
import numpy as np
import pygame

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")


def ensure_mixer():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        return True
    except pygame.error:
        return False


def find_sound_file(stem):
    for ext in (".wav", ".mp3", ".ogg"):
        path = os.path.join(SOUNDS_DIR, f"{stem}{ext}")
        if os.path.exists(path):
            return path
    return None


ensure_mixer()


def load_sound(path):
    if not ensure_mixer():
        return None
    if path and os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            return None
    return None


shoot_sound = load_sound(find_sound_file("shoot"))
ice_cast_sound = load_sound(find_sound_file("ice_cast"))
hit_sound = load_sound(find_sound_file("hit"))
hurt_sound = load_sound(find_sound_file("hurt"))
boss_sound = load_sound(find_sound_file("boss"))
freeze_sound = load_sound(find_sound_file("freeze"))


def load_image(path, size):
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            return cv2.resize(img, size)
    return None


def clamp_overlay(frame, x, y, img):
    x = int(max(0, min(x, frame.shape[1] - img.shape[1])))
    y = int(max(0, min(y, frame.shape[0] - img.shape[0])))
    cvzone.overlayPNG(frame, img, [x, y])


def apply_frost_tint(frame, center, radius, alpha=0.26):
    overlay = frame.copy()
    cv2.circle(overlay, center, radius, (255, 255, 170), -1)
    cv2.circle(overlay, center, int(radius * 0.72), (255, 240, 120), -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


img_player = load_image("assets/images/player.png", (80, 80))
img_shuriken = load_image("assets/images/shuriken.png", (40, 40))
img_enemy = load_image("assets/images/enemy.png", (60, 60))
img_boss = load_image("assets/images/boss.png", (150, 150))
img_fireball = load_image("assets/images/fireball.png", (40, 40))


class Shuriken:
    def __init__(self, x, y, dx=15, dy=0, damage=1):
        self.x, self.y = x, y
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.glow_radius = 16

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, frame):
        center = (int(self.x), int(self.y))
        cv2.circle(frame, center, self.glow_radius, (0, 210, 255), 1)
        if img_shuriken is not None:
            clamp_overlay(frame, self.x - img_shuriken.shape[1] // 2, self.y - img_shuriken.shape[0] // 2, img_shuriken)
        else:
            cv2.circle(frame, center, 10, (0, 220, 255), 2)
            cv2.circle(frame, center, 4, (255, 255, 255), -1)


class IceShard:
    def __init__(self, x, y, dx=11, dy=0, damage=1, freeze_time=1.8, slow_factor=0.35):
        self.x, self.y = x, y
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.freeze_time = freeze_time
        self.slow_factor = slow_factor
        self.phase = random.random() * math.pi * 2
        self.trail = []

    def move(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        self.x += self.dx
        self.y += self.dy
        self.phase += 0.35

    def draw(self, frame):
        for i, (tx, ty) in enumerate(self.trail):
            radius = max(5, 13 - (len(self.trail) - i))
            color = (255, 220 + min(i * 4, 35), 140 + min(i * 10, 100))
            cv2.circle(frame, (int(tx), int(ty)), radius, color, 1)
        center = (int(self.x), int(self.y))
        wing = int(10 + 3 * math.sin(self.phase))
        points = np.array(
            [
                (center[0] + wing, center[1]),
                (center[0], center[1] - 17),
                (center[0] - wing, center[1]),
                (center[0], center[1] + 17),
            ],
            dtype=np.int32,
        )
        cv2.fillConvexPoly(frame, points, (255, 255, 190))
        cv2.polylines(frame, [points], True, (255, 255, 255), 2)
        cv2.circle(frame, center, 24, (255, 245, 160), 1)
        cv2.circle(frame, center, 12, (255, 255, 255), 1)


class Bullet:
    def __init__(self, x, y, speed=12, dy=0, radius=7):
        self.x, self.y = x, y
        self.speed = speed
        self.dy = dy
        self.radius = radius
        self.trail = []

    def move(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 4:
            self.trail.pop(0)
        self.x -= self.speed
        self.y += self.dy

    def draw(self, frame):
        for i, (tx, ty) in enumerate(self.trail):
            cv2.circle(frame, (int(tx), int(ty)), 3 + i, (0, 130, 255), 1)
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, (0, 165, 255), -1)
        cv2.circle(frame, (int(self.x), int(self.y)), max(2, self.radius // 2), (255, 255, 255), -1)


class LaserBeam:
    def __init__(self, y, duration=1.2):
        self.y = y
        self.duration = duration
        self.created_at = time.time()

    def is_active(self):
        return time.time() - self.created_at < self.duration

    def collides_with(self, x, y):
        return abs(y - self.y) < 24 and x > 180

    def draw(self, frame):
        pulse = 120 + int(80 * math.sin((time.time() - self.created_at) * 18))
        cv2.line(frame, (190, int(self.y)), (frame.shape[1], int(self.y)), (0, 80, 255), 6)
        cv2.line(frame, (190, int(self.y)), (frame.shape[1], int(self.y)), (pulse, 220, 255), 2)


class IceBurst:
    def __init__(self, x, y, radius=18):
        self.x = x
        self.y = y
        self.radius = radius
        self.life = 12
        self.max_life = 12
        self.spark_angles = [random.random() * math.pi * 2 for _ in range(8)]

    def update(self):
        self.life -= 1
        self.radius += 4
        return self.life > 0

    def draw(self, frame):
        ratio = max(0.0, self.life / self.max_life)
        center = (int(self.x), int(self.y))
        outer = int(self.radius)
        inner = max(4, int(self.radius * 0.45))
        cv2.circle(frame, center, outer, (255, 245, 180), 2)
        cv2.circle(frame, center, inner, (255, 255, 255), 1)
        for angle in self.spark_angles:
            dist = outer + 10 * ratio
            sx = int(self.x + math.cos(angle) * dist)
            sy = int(self.y + math.sin(angle) * dist)
            cv2.line(frame, center, (sx, sy), (255, 255, 180), 1)
            cv2.circle(frame, (sx, sy), 2, (255, 255, 255), -1)


class UltimateBurst:
    def __init__(self, x, y, radius=120):
        self.x = x
        self.y = y
        self.radius = radius
        self.life = 18
        self.max_life = 18

    def update(self):
        self.life -= 1
        self.radius += 18
        return self.life > 0

    def draw(self, frame):
        ratio = max(0.0, self.life / self.max_life)
        center = (int(self.x), int(self.y))
        cv2.circle(frame, center, int(self.radius), (255, 250, 180), 3)
        cv2.circle(frame, center, int(self.radius * 0.7), (255, 220, 120), 2)
        spokes = 12
        for idx in range(spokes):
            angle = (idx / spokes) * math.pi * 2 + time.time() * 2.2
            sx = int(self.x + math.cos(angle) * self.radius)
            sy = int(self.y + math.sin(angle) * self.radius)
            cv2.line(frame, center, (sx, sy), (255, 255, int(120 + 100 * ratio)), 1)


class HealthOrb:
    def __init__(self, x, y, heal_amount=2, fall_speed=3.2):
        self.x = x
        self.y = y
        self.heal_amount = heal_amount
        self.phase = random.random() * math.pi * 2
        self.fall_speed = fall_speed

    def update(self):
        self.phase += 0.18
        self.y += self.fall_speed

    def draw(self, frame):
        center = (int(self.x), int(self.y + math.sin(self.phase) * 4))
        cv2.circle(frame, center, 20, (80, 120, 255), 2)
        cv2.circle(frame, center, 15, (40, 50, 220), -1)
        cv2.circle(frame, center, 6, (255, 255, 255), -1)
        cv2.rectangle(frame, (center[0] - 3, center[1] - 10), (center[0] + 3, center[1] + 10), (255, 255, 255), -1)
        cv2.rectangle(frame, (center[0] - 10, center[1] - 3), (center[0] + 10, center[1] + 3), (255, 255, 255), -1)


class ShieldOrb:
    def __init__(self, x, y, shield_time=2.0, fall_speed=3.6):
        self.x = x
        self.y = y
        self.shield_time = shield_time
        self.phase = random.random() * math.pi * 2
        self.fall_speed = fall_speed

    def update(self):
        self.phase += 0.22
        self.y += self.fall_speed

    def draw(self, frame):
        center = (int(self.x), int(self.y + math.sin(self.phase) * 4))
        cv2.circle(frame, center, 21, (255, 230, 90), 2)
        shield = np.array(
            [
                (center[0], center[1] - 14),
                (center[0] + 12, center[1] - 6),
                (center[0] + 9, center[1] + 10),
                (center[0], center[1] + 16),
                (center[0] - 9, center[1] + 10),
                (center[0] - 12, center[1] - 6),
            ],
            dtype=np.int32,
        )
        cv2.fillConvexPoly(frame, shield, (0, 210, 255))
        cv2.polylines(frame, [shield], True, (255, 255, 255), 2)


class Ninja:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = 5
        self.max_hp = 5
        self.defending = False
        self.shield_until = 0
        self.last_attack = {"1": 0, "2": 0, "3": 0, "5": 0}
        self.base_cooldown = {"1": 0.3, "2": 0.6, "3": 1.0, "5": 9.0}
        self.combo_damage_bonus = 0
        self.combo_cooldown_scale = 1.0
        self.shuriken_bonus = 0
        self.freeze_bonus = 0.0
        self.item_magnet = 0
        self.shield_bonus = 0.0
        self.damage_bonus = 0
        self.ultimate_charge = 0
        self.ultimate_max = 100
        self.last_ultimate = 0

    def update_position(self, x, y):
        self.x = max(30, min(x, 770))
        self.y = max(30, min(y, 570))

    def set_combo_bonus(self, damage_bonus, cooldown_scale):
        self.combo_damage_bonus = damage_bonus
        self.combo_cooldown_scale = cooldown_scale

    def gain_ultimate(self, amount):
        self.ultimate_charge = min(self.ultimate_max, self.ultimate_charge + amount)

    def can_attack(self, finger):
        now = time.time()
        cooldown = self.base_cooldown[str(finger)]
        if finger != 5:
            cooldown *= self.combo_cooldown_scale
        return now - self.last_attack[str(finger)] >= cooldown

    def has_shield(self):
        return time.time() < self.shield_until

    def activate_shield(self, duration):
        self.shield_until = max(self.shield_until, time.time() + duration + self.shield_bonus)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def get_damage_bonus(self):
        return self.damage_bonus + self.combo_damage_bonus

    def attack(self, finger):
        if finger == 5:
            if self.ultimate_charge < self.ultimate_max or not self.can_attack(5):
                return []
            self.last_attack["5"] = time.time()
            self.ultimate_charge = 0
            return [UltimateWave(self.x + 40, self.y, damage=5 + self.get_damage_bonus())]

        if not self.can_attack(finger):
            return []
        self.last_attack[str(finger)] = time.time()
        bullets = []
        bonus_damage = self.get_damage_bonus()
        if finger == 1:
            count = 1 + self.shuriken_bonus
            offsets = spread_offsets(count, 12)
            for dy in offsets:
                bullets.append(Shuriken(self.x + 40, self.y + dy, damage=1 + bonus_damage))
        elif finger == 2:
            count = 3 + self.shuriken_bonus
            offsets = spread_offsets(count, 16)
            for dy in offsets:
                bullets.append(Shuriken(self.x + 40, self.y + dy, dx=15, dy=0, damage=1 + bonus_damage))
        elif finger == 3:
            count = 5 + self.shuriken_bonus
            offsets = spread_offsets(count, 20)
            for dy in offsets:
                bullets.append(
                    IceShard(
                        self.x + 45,
                        self.y + dy,
                        dx=11,
                        dy=0,
                        damage=1 + bonus_damage,
                        freeze_time=1.8 + self.freeze_bonus,
                    )
                )
        if finger == 3 and ice_cast_sound:
            ice_cast_sound.play()
        elif shoot_sound:
            shoot_sound.play()
        return bullets

    def draw(self, frame):
        percent = self.hp / self.max_hp
        cv2.rectangle(frame, (self.x - 40, self.y - 50), (self.x + 40, self.y - 40), (0, 0, 0), -1)
        cv2.rectangle(frame, (self.x - 40, self.y - 50), (self.x - 40 + int(80 * percent), self.y - 40), (0, 255, 0), -1)
        if self.defending:
            cv2.circle(frame, (self.x, self.y), 60, (255, 255, 0), 3)
        if self.has_shield():
            cv2.circle(frame, (self.x, self.y), 48, (255, 230, 90), 2)
            cv2.circle(frame, (self.x, self.y), 58, (0, 220, 255), 2)
        if img_player is not None:
            clamp_overlay(frame, self.x - img_player.shape[1] // 2, self.y - img_player.shape[0] // 2, img_player)
        else:
            cv2.circle(frame, (self.x, self.y), 25, (255, 0, 0), -1)


class Enemy:
    def __init__(self, x, y, hp, speed):
        self.x, self.y = x, y
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.last_shot = time.time()
        self.freeze_until = 0
        self.slow_factor = 1.0
        self.tint_phase = random.random() * math.pi * 2

    def is_frozen(self):
        return time.time() < self.freeze_until

    def apply_freeze(self, duration, slow_factor):
        self.freeze_until = max(self.freeze_until, time.time() + duration)
        self.slow_factor = min(self.slow_factor, slow_factor)

    def update_status(self):
        self.tint_phase += 0.25
        if not self.is_frozen():
            self.slow_factor = 1.0

    def move(self):
        self.update_status()
        self.x -= self.speed * self.slow_factor

    def shoot(self, level, difficulty_factor):
        delay = 1.0 / (level * 0.2 + 0.5) * difficulty_factor
        if self.is_frozen():
            delay *= 1.8
        if time.time() - self.last_shot > delay:
            self.last_shot = time.time()
            return Bullet(self.x - 20, self.y, speed=8)
        return None

    def draw(self, frame):
        center = (int(self.x), int(self.y))
        if img_enemy is not None:
            clamp_overlay(frame, self.x - img_enemy.shape[1] // 2, self.y - img_enemy.shape[0] // 2, img_enemy)
        else:
            cv2.rectangle(frame, (int(self.x - 20), int(self.y - 20)), (int(self.x + 20), int(self.y + 20)), (0, 0, 255), -1)
        hp_w = int((self.hp / self.max_hp) * 40)
        cv2.rectangle(frame, (int(self.x - 20), int(self.y - 30)), (int(self.x + 20), int(self.y - 25)), (0, 0, 0), -1)
        cv2.rectangle(frame, (int(self.x - 20), int(self.y - 30)), (int(self.x - 20 + hp_w), int(self.y - 25)), (0, 255, 0), -1)
        if self.is_frozen():
            apply_frost_tint(frame, center, 26, 0.32)
            pulse = 50 + int(30 * math.sin(self.tint_phase))
            cv2.circle(frame, center, 34, (255, 220, 120 + pulse), 2)
            cv2.putText(frame, "FREEZE", (int(self.x - 28), int(self.y - 38)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 180), 1)


class Boss:
    def __init__(self, x, y, hp, level):
        self.x, self.y = x, y
        self.hp = hp
        self.max_hp = hp
        self.level = level
        self.start_time = time.time()
        self.last_shot = time.time()
        self.freeze_until = 0
        self.slow_factor = 1.0
        self.tint_phase = random.random() * math.pi * 2
        self.phase_two = False
        self.last_fan = time.time()
        self.last_laser = time.time()
        self.last_summon = time.time()

    def is_frozen(self):
        return time.time() < self.freeze_until

    def apply_freeze(self, duration, slow_factor):
        self.freeze_until = max(self.freeze_until, time.time() + duration)
        self.slow_factor = min(self.slow_factor, slow_factor)

    def update_status(self):
        self.tint_phase += 0.2
        if not self.is_frozen():
            self.slow_factor = 1.0
        if self.hp <= self.max_hp * 0.3:
            self.phase_two = True

    def move(self):
        self.update_status()
        amp = 150 * (0.65 if self.is_frozen() else 1.0)
        speed = (2.1 if self.phase_two else 1.4) * (0.55 if self.is_frozen() else 1.0)
        self.y = 300 + amp * math.sin((time.time() - self.start_time) * speed)

    def act(self):
        bullets = []
        lasers = []
        summons = 0
        now = time.time()
        frozen_factor = 1.5 if self.is_frozen() else 1.0

        if now - self.last_fan > 1.7 * frozen_factor:
            self.last_fan = now
            fan = [-4, -2, 0, 2, 4] if not self.phase_two else [-6, -4, -2, 0, 2, 4, 6]
            for dy in fan:
                bullets.append(Bullet(self.x - 60, self.y + dy * 4, speed=11 + self.level, dy=dy))

        if now - self.last_laser > 5.2 * frozen_factor:
            self.last_laser = now
            lasers.append(LaserBeam(self.y, duration=1.0 if self.phase_two else 0.8))

        if now - self.last_summon > 7.0 * frozen_factor:
            self.last_summon = now
            summons = 2 if self.phase_two else 1

        return bullets, lasers, summons

    def draw(self, frame):
        center = (int(self.x), int(self.y))
        if img_boss is not None:
            clamp_overlay(frame, self.x - img_boss.shape[1] // 2, self.y - img_boss.shape[0] // 2, img_boss)
        else:
            cv2.rectangle(frame, (int(self.x - 60), int(self.y - 60)), (int(self.x + 60), int(self.y + 60)), (128, 0, 128), -1)
        hp_w = int((self.hp / self.max_hp) * 200)
        cv2.rectangle(frame, (int(self.x - 100), int(self.y - 80)), (int(self.x + 100), int(self.y - 70)), (0, 0, 0), -1)
        cv2.rectangle(frame, (int(self.x - 100), int(self.y - 80)), (int(self.x - 100 + hp_w), int(self.y - 70)), (0, 255, 0), -1)
        phase_text = "PHASE 2" if self.phase_two else "PHASE 1"
        cv2.putText(frame, f"BOSS Lv.{self.level} {phase_text}", (int(self.x - 78), int(self.y - 92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        if self.is_frozen():
            apply_frost_tint(frame, center, 72, 0.22)
            pulse = 70 + int(30 * math.sin(self.tint_phase))
            cv2.circle(frame, center, 92, (255, 240, 120 + pulse), 3)
            cv2.putText(frame, "ICE LOCK", (int(self.x - 42), int(self.y - 105)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 200), 2)


class UltimateWave:
    def __init__(self, x, y, damage=5):
        self.x = x
        self.y = y
        self.damage = damage
        self.radius = 65
        self.max_radius = 360
        self.already_hit = set()

    def move(self):
        self.radius += 26

    def is_finished(self):
        return self.radius >= self.max_radius

    def draw(self, frame):
        center = (int(self.x), int(self.y))
        cv2.circle(frame, center, int(self.radius), (255, 240, 170), 3)
        cv2.circle(frame, center, int(self.radius * 0.72), (255, 255, 255), 1)


def spread_offsets(count, spacing):
    center = (count - 1) / 2
    return [int((idx - center) * spacing) for idx in range(count)]
