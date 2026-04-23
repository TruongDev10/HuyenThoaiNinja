import cv2
import time
import random
import pygame
import os
from src.hand_tracker import HandTracker
from src.game_entities import *

# -------------------- LẤY KÍCH THƯỚC MÀN HÌNH --------------------
try:
    from tkinter import Tk
    root = Tk()
    SCREEN_W = root.winfo_screenwidth()
    SCREEN_H = root.winfo_screenheight()
    root.destroy()
except:
    SCREEN_W, SCREEN_H = 1366, 768  # fallback

# Kích thước logic game (vẫn giữ 800x600 để tính toán va chạm)
GAME_W, GAME_H = 800, 600

# -------------------- KHỞI TẠO ÂM THANH --------------------
pygame.mixer.init()
if os.path.exists("assets/sounds/background.mp3"):
    pygame.mixer.music.load("assets/sounds/background.mp3")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

# -------------------- MENU CHỌN ĐỘ KHÓ BẰNG TAY (FULL MÀN HÌNH) --------------------
def show_menu_by_hand():
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    selected = "easy"
    confirmed = False

    cv2.namedWindow("Menu", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Menu", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))

        # Resize về kích thước logic để nhận diện tay
        small = cv2.resize(frame, (GAME_W, GAME_H))
        found, _, _, fingers = tracker.get_player_action(small, GAME_W, GAME_H)

        if found:
            if fingers == 1:
                selected = "easy"
            elif fingers == 2:
                selected = "medium"
            elif fingers == 3:
                selected = "hard"
            elif fingers == 0:
                confirmed = True
                break

        # Vẽ menu lên full màn hình
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (SCREEN_W, SCREEN_H), (0,0,0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        scale = SCREEN_W / 800  # hệ số co dãn chữ
        cv2.putText(frame, "CHON DO KHO BANG TAY", (int(SCREEN_W//2 - 200*scale), int(80*scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2*scale, (0,255,255), 3)
        cv2.putText(frame, "1 ngon: DE", (int(SCREEN_W//2 - 100*scale), int(180*scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1*scale, (255,255,255) if selected=="easy" else (150,150,150), 2)
        cv2.putText(frame, "2 ngon: TRUNG BINH", (int(SCREEN_W//2 - 120*scale), int(260*scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1*scale, (255,255,255) if selected=="medium" else (150,150,150), 2)
        cv2.putText(frame, "3 ngon: KHO", (int(SCREEN_W//2 - 80*scale), int(340*scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1*scale, (255,255,255) if selected=="hard" else (150,150,150), 2)
        cv2.putText(frame, "NAM TAY (0 ngon) -> XAC NHAN", (int(SCREEN_W//2 - 220*scale), int(450*scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8*scale, (0,255,0), 2)
        cv2.putText(frame, f"Dang chon: {selected.upper()}", (int(SCREEN_W//2 - 120*scale), int(520*scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8*scale, (0,255,255), 2)
        if found:
            cv2.putText(frame, f"So ngon: {fingers}", (int(20*scale), int(50*scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8*scale, (0,200,0), 2)

        cv2.imshow("Menu", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return selected if confirmed else None

# -------------------- CẤU HÌNH ĐỘ KHÓ --------------------
DIFFICULTY = {
    "easy":   {"enemy_speed":3, "enemy_hp":1, "spawn_delay":1.8, "boss_hp_mult":0.8, "bullet_factor":1.0},
    "medium": {"enemy_speed":4, "enemy_hp":2, "spawn_delay":1.2, "boss_hp_mult":1.0, "bullet_factor":1.2},
    "hard":   {"enemy_speed":6, "enemy_hp":3, "spawn_delay":0.8, "boss_hp_mult":1.5, "bullet_factor":1.5}
}

# -------------------- MAIN GAME (FULL MÀN HÌNH) --------------------
def main():
    difficulty = show_menu_by_hand()
    if difficulty is None:
        return
    cfg = DIFFICULTY[difficulty]

    cap = cv2.VideoCapture(0)
    tracker = HandTracker()

    # Nền (tùy chọn)
    bg = None
    if os.path.exists("assets/images/background.jpg"):
        bg = cv2.imread("assets/images/background.jpg")
        bg = cv2.resize(bg, (GAME_W, GAME_H))

    # Khởi tạo game
    ninja = Ninja(100, GAME_H//2)
    score = 0
    level = 0
    shurikens = []
    enemies = []
    bullets = []
    boss = None
    game_over = False
    last_spawn = time.time()
    combo = 0
    last_combo_time = time.time()

    # Tạo cửa sổ full màn hình
    cv2.namedWindow("Huyen thoai Ninja", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Huyen thoai Ninja", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        # Resize về kích thước logic để xử lý
        small_frame = cv2.resize(frame, (GAME_W, GAME_H))

        # -------------------- MÀN HÌNH GAME OVER --------------------
        if game_over:
            display = cv2.resize(small_frame, (SCREEN_W, SCREEN_H))
            if bg is not None:
                bg_full = cv2.resize(bg, (SCREEN_W, SCREEN_H))
                display = cv2.addWeighted(bg_full, 0.5, display, 0.5, 0)
            scale = SCREEN_W / 800
            cv2.putText(display, "GAME OVER!", (int(SCREEN_W//2 - 150*scale), int(SCREEN_H//2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 2*scale, (0,0,255), 5)
            cv2.putText(display, f"Diem: {score}  Level: {level+1}", (int(SCREEN_W//2 - 150*scale), int(SCREEN_H//2 + 60*scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1*scale, (255,255,255), 2)
            cv2.putText(display, "Nhan 'R' choi lai | 'Q' thoat", (int(SCREEN_W//2 - 200*scale), int(SCREEN_H//2 + 120*scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7*scale, (255,255,0), 2)
            cv2.imshow("Huyen thoai Ninja", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                ninja = Ninja(100, GAME_H//2)
                score = 0
                level = 0
                shurikens.clear()
                enemies.clear()
                bullets.clear()
                boss = None
                game_over = False
                combo = 0
                last_spawn = time.time()
            elif key == ord('q'):
                break
            continue

        # -------------------- NHẬN DIỆN TAY & TẤN CÔNG --------------------
        found, px, py, fingers = tracker.get_player_action(small_frame, GAME_W, GAME_H)
        if found:
            ninja.update_position(px, py)
            ninja.defending = (fingers == 0)
            if fingers in [1,2,3] and not ninja.defending:
                atk_list = ninja.attack(fingers)
                shurikens.extend(atk_list)

        # -------------------- SPAWN ENEMY --------------------
        if boss is None:
            if time.time() - last_spawn > cfg["spawn_delay"] / (level+1):
                hp = cfg["enemy_hp"] + level//3
                spd = cfg["enemy_speed"] + level//5
                enemies.append(Enemy(GAME_W, random.randint(50, GAME_H-50), hp, spd))
                last_spawn = time.time()

        # -------------------- SPAWN BOSS --------------------
        if score > 0 and score % 20 == 0 and boss is None:
            boss_hp = int(50 * (level+1) * cfg["boss_hp_mult"])
            boss = Boss(GAME_W-100, GAME_H//2, boss_hp, level+1)
            enemies.clear()
            if 'boss_sound' in globals() and boss_sound:
                boss_sound.play()

        # -------------------- CẬP NHẬT ĐẠN CỦA PLAYER --------------------
        for s in shurikens[:]:
            s.move()
            if s.x > GAME_W:
                shurikens.remove(s)

        # -------------------- ĐẠN CỦA ENEMY --------------------
        for b in bullets[:]:
            b.move()
            if b.x < 0:
                bullets.remove(b)
            elif abs(b.x - ninja.x) < 30 and abs(b.y - ninja.y) < 30:
                if not ninja.defending:
                    ninja.hp -= 1
                    combo = 0
                    if 'hurt_sound' in globals() and hurt_sound:
                        hurt_sound.play()
                bullets.remove(b)
                if ninja.hp <= 0:
                    game_over = True

        # -------------------- ENEMY --------------------
        for e in enemies[:]:
            e.move()
            shot = e.shoot(level+1, cfg["bullet_factor"])
            if shot:
                bullets.append(shot)
            for s in shurikens[:]:
                if abs(s.x - e.x) < 40 and abs(s.y - e.y) < 40:
                    e.hp -= s.damage
                    shurikens.remove(s)
                    if 'hit_sound' in globals() and hit_sound:
                        hit_sound.play()
                    break
            if e.hp <= 0:
                score += 1
                combo += 1
                last_combo_time = time.time()
                enemies.remove(e)
            elif e.x < 0:
                enemies.remove(e)

        # -------------------- BOSS --------------------
        if boss:
            boss.move()
            bullets_shot = boss.shoot()
            if bullets_shot:
                bullets.extend(bullets_shot)
            for s in shurikens[:]:
                if abs(s.x - boss.x) < 80 and abs(s.y - boss.y) < 80:
                    boss.hp -= s.damage
                    shurikens.remove(s)
                    if 'hit_sound' in globals() and hit_sound:
                        hit_sound.play()
                    break
            if boss.hp <= 0:
                score += 10
                level += 1
                boss = None

        # -------------------- RESET COMBO --------------------
        if time.time() - last_combo_time > 3:
            combo = 0

        # -------------------- VẼ LÊN FRAME LOGIC --------------------
        if bg is not None:
            small_frame = cv2.addWeighted(bg, 0.8, small_frame, 0.2, 0)

        ninja.draw(small_frame)
        for s in shurikens: s.draw(small_frame)
        for e in enemies: e.draw(small_frame)
        for b in bullets: b.draw(small_frame)
        if boss: boss.draw(small_frame)

        # UI
        cv2.putText(small_frame, f"HP: {ninja.hp}/{ninja.max_hp}", (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0) if ninja.hp>2 else (0,0,255), 2)
        cv2.putText(small_frame, f"Diem: {score}", (20,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(small_frame, f"Level: {level+1}", (GAME_W-120,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        cv2.putText(small_frame, f"Combo: x{combo}", (GAME_W-120,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,0,255), 2)
        cv2.putText(small_frame, f"So ngon: {fingers}", (20,120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
        cv2.putText(small_frame, "1 ngon: 1 shuriken", (20, GAME_H-60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.putText(small_frame, "2 ngon: 3 shuriken", (20, GAME_H-40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.putText(small_frame, "3 ngon: 5 fireball", (20, GAME_H-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
        cv2.putText(small_frame, "0 ngon: Phong thu", (GAME_W-150, GAME_H-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

        # -------------------- SCALE LÊN FULL MÀN HÌNH --------------------
        display_frame = cv2.resize(small_frame, (SCREEN_W, SCREEN_H))
        cv2.imshow("Huyen thoai Ninja", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pygame.mixer.music.stop()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()