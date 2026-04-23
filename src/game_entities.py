import random
import time
import math
import cv2
import cvzone
import os
import pygame

# Khởi tạo âm thanh (sẽ được gọi từ main, nhưng để tránh lỗi ta khởi tạo ở đây)
pygame.mixer.init()

def load_sound(path):
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

# Tải âm thanh (cần tạo thư mục assets/sounds/ và thêm file .wav)
shoot_sound = load_sound("assets/sounds/shoot.wav")
hit_sound = load_sound("assets/sounds/hit.wav")
hurt_sound = load_sound("assets/sounds/hurt.wav")
boss_sound = load_sound("assets/sounds/boss.wav")

def load_image(path, size):
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            return cv2.resize(img, size)
    return None

img_player = load_image("assets/images/player.png", (80,80))
img_shuriken = load_image("assets/images/shuriken.png", (40,40))
img_enemy = load_image("assets/images/enemy.png", (60,60))
img_boss = load_image("assets/images/boss.png", (150,150))
img_fireball = load_image("assets/images/fireball.png", (40,40))
img_double = load_image("assets/images/double_shuriken.png", (30,30))

class Shuriken:
    def __init__(self, x, y, dx=15, dy=0):
        self.x, self.y = x, y
        self.dx = dx
        self.dy = dy
        self.speed = 15
        self.damage = 1
    def move(self):
        self.x += self.dx
        self.y += self.dy
    def draw(self, frame):
        if img_shuriken is not None:
            x_pos = self.x - img_shuriken.shape[1]//2
            y_pos = self.y - img_shuriken.shape[0]//2
            cvzone.overlayPNG(frame, img_shuriken, [x_pos, y_pos])
        else:
            cv2.circle(frame, (int(self.x), int(self.y)), 8, (0,255,255), -1)

class Fireball:
    def __init__(self, x, y, dx=12, dy=0):
        self.x, self.y = x, y
        self.dx = dx
        self.dy = dy
        self.damage = 2
    def move(self):
        self.x += self.dx
        self.y += self.dy
    def draw(self, frame):
        if img_fireball is not None:
            x_pos = self.x - img_fireball.shape[1]//2
            y_pos = self.y - img_fireball.shape[0]//2
            cvzone.overlayPNG(frame, img_fireball, [x_pos, y_pos])
        else:
            cv2.circle(frame, (int(self.x), int(self.y)), 12, (0,0,255), -1)
            cv2.circle(frame, (int(self.x), int(self.y)), 6, (0,100,255), -1)

class Ninja:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = 5
        self.max_hp = 5
        self.defending = False
        self.last_attack = {'1':0, '2':0, '3':0}
        self.cooldown = {'1':0.3, '2':0.6, '3':0.9}  # giảm cooldown để bắn nhiều hơn
    def update_position(self, x, y):
        self.x = max(30, min(x, 770))
        self.y = max(30, min(y, 570))
    def can_attack(self, finger):
        now = time.time()
        return now - self.last_attack[str(finger)] >= self.cooldown[str(finger)]
    def attack(self, finger):
        if not self.can_attack(finger):
            return []
        self.last_attack[str(finger)] = time.time()
        bullets = []
        if finger == 1:
            # 1 phi tiêu
            bullets.append(Shuriken(self.x+40, self.y))
            if shoot_sound: shoot_sound.play()
        elif finger == 2:
            # 3 phi tiêu, rải theo chiều dọc
            for dy in [-20, 0, 20]:
                bullets.append(Shuriken(self.x+40, self.y+dy, dx=15, dy=0))
            if shoot_sound: shoot_sound.play()
        elif finger == 3:
            # 5 quả cầu lửa, rải rộng hơn
            for dy in [-40, -20, 0, 20, 40]:
                bullets.append(Fireball(self.x+40, self.y+dy, dx=12, dy=0))
            if shoot_sound: shoot_sound.play()
        return bullets
    def draw(self, frame):
        bar_w = 80
        bar_h = 10
        percent = self.hp/self.max_hp
        cv2.rectangle(frame, (self.x-40, self.y-50), (self.x-40+bar_w, self.y-40), (0,0,0), -1)
        cv2.rectangle(frame, (self.x-40, self.y-50), (self.x-40+int(bar_w*percent), self.y-40), (0,255,0), -1)
        if self.defending:
            cv2.circle(frame, (self.x, self.y), 60, (255,255,0), 3)
        if img_player is not None:
            x_pos = self.x - img_player.shape[1]//2
            y_pos = self.y - img_player.shape[0]//2
            cvzone.overlayPNG(frame, img_player, [x_pos, y_pos])
        else:
            cv2.circle(frame, (self.x, self.y), 25, (255,0,0), -1)

class Enemy:
    def __init__(self, x, y, hp, speed):
        self.x, self.y = x, y
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.last_shot = time.time()
    def move(self):
        self.x -= self.speed
    def shoot(self, level, difficulty_factor):
        delay = 1.0 / (level * 0.2 + 0.5) * difficulty_factor
        if time.time() - self.last_shot > delay:
            self.last_shot = time.time()
            return Bullet(self.x-20, self.y, speed=8)
        return None
    def draw(self, frame):
        if img_enemy is not None:
            x_pos = self.x - img_enemy.shape[1]//2
            y_pos = self.y - img_enemy.shape[0]//2
            cvzone.overlayPNG(frame, img_enemy, [x_pos, y_pos])
        else:
            cv2.rectangle(frame, (self.x-20, self.y-20), (self.x+20, self.y+20), (0,0,255), -1)
        hp_w = int((self.hp/self.max_hp)*40)
        cv2.rectangle(frame, (self.x-20, self.y-30), (self.x+20, self.y-25), (0,0,0), -1)
        cv2.rectangle(frame, (self.x-20, self.y-30), (self.x-20+hp_w, self.y-25), (0,255,0), -1)

class Boss:
    def __init__(self, x, y, hp, level):
        self.x, self.y = x, y
        self.hp = hp
        self.max_hp = hp
        self.level = level
        self.start_time = time.time()
        self.last_shot = time.time()
    def move(self):
        self.y = 300 + 150 * math.sin((time.time()-self.start_time)*1.5)
    def shoot(self):
        if time.time() - self.last_shot > 1.0:
            self.last_shot = time.time()
            bullets = []
            for dy in [-40, -20, 0, 20, 40]:
                bullets.append(Bullet(self.x-60, self.y+dy, speed=12))
            return bullets
        return None
    def draw(self, frame):
        if img_boss is not None:
            x_pos = self.x - img_boss.shape[1]//2
            y_pos = self.y - img_boss.shape[0]//2
            cvzone.overlayPNG(frame, img_boss, [x_pos, y_pos])
        else:
            cv2.rectangle(frame, (self.x-60, self.y-60), (self.x+60, self.y+60), (128,0,128), -1)
        hp_w = int((self.hp/self.max_hp)*200)
        cv2.rectangle(frame, (self.x-100, self.y-80), (self.x+100, self.y-70), (0,0,0), -1)
        cv2.rectangle(frame, (self.x-100, self.y-80), (self.x-100+hp_w, self.y-70), (0,255,0), -1)
        cv2.putText(frame, f"BOSS Lv.{self.level}", (self.x-50, self.y-90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

class Bullet:
    def __init__(self, x, y, speed=12):
        self.x, self.y = x, y
        self.speed = speed
    def move(self):
        self.x -= self.speed
    def draw(self, frame):
        cv2.circle(frame, (self.x, self.y), 6, (0,165,255), -1)