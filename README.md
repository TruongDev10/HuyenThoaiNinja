<h2 align ="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>

<h2 align ="center">  
   🥷 HUYỀN THOẠI NINJA – GAME ĐIỀU KHIỂN BẰNG CỬ CHỈ TAY QUA CAMERA
</h2>

<div align ="center">
    <p align ="center">
        <img src="https://github.com/tiennq004/LTM_he_thong_canh_bao_thoi_gian_thuc/blob/main/docs/aiotlab_logo.png" width="170"/>
        <img src="https://github.com/tiennq004/LTM_he_thong_canh_bao_thoi_gian_thuc/blob/main/docs/fitdnu_logo.png" width="180"/>
        <img src="https://github.com/tiennq004/LTM_he_thong_canh_bao_thoi_gian_thuc/blob/main/docs/dnu_logo.png" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)
</div>

---

## 📖 1. Giới thiệu game

- **Huyền Thoại Ninja** là một trò chơi hành động 2D kết hợp công nghệ **AI nhận diện cử chỉ tay (Hand Tracking)**.

- Người chơi sử dụng webcam để điều khiển nhân vật ninja thay vì bàn phím, tạo trải nghiệm tương tác mới lạ.

- 🎯 Mục tiêu:
  - Điều khiển ninja tiêu diệt kẻ địch
  - Né tránh nguy hiểm
  - Sống sót và đạt điểm cao nhất

---

### 🎮 Gameplay

- ✋ Điều khiển bằng tay qua camera  
- 🥷 Di chuyển nhân vật theo cử chỉ  
- 🗡️ Ném shuriken tiêu diệt enemy  
- 👾 Đối đầu với boss  
- 🔊 Hiệu ứng âm thanh sống động  

---

### 🔥 Đặc điểm nổi bật

- Không cần bàn phím (AI điều khiển bằng tay)  
- Gameplay nhanh, phản xạ cao  
- Có hệ thống enemy và boss  
- Âm thanh đa dạng (attack, hit, boss theme)  

---

### 🖥️ Cấu trúc hệ thống

- 🎨 **Giao diện (UI)**  
  - Hiển thị nhân vật, background, hiệu ứng  

- 🧠 **Game Logic**  
  - Xử lý va chạm  
  - Điều khiển nhân vật  
  - Quản lý enemy / boss  

- 🤖 **AI Hand Tracking**  
  - Nhận diện cử chỉ tay  
  - Điều khiển hành động trong game  

---

## 🔧 2. Công nghệ & Công cụ sử dụng

- Ngôn ngữ:  
  <img src="https://www.python.org/static/community_logos/python-logo.png" width="80"/>

- Thư viện:
  - Pygame (Game 2D)
  - OpenCV (Camera)
  - MediaPipe (Hand Tracking)

- Công cụ:
  - VS Code
  - Git & GitHub

- Hệ điều hành:
  - Windows 10/11

---

## 🚀 3. Hình ảnh các chức năng chính

<p align="center">
  <img src="assets/images/player.png" width="600"/>
</p>
<p align="center"><em>Nhân vật ninja</em></p>

<p align="center">
  <img src="assets/images/enemy.png" width="600"/>
</p>
<p align="center"><em>Kẻ địch</em></p>

<p align="center">
  <img src="assets/images/shuriken.png" width="600"/>
</p>
<p align="center"><em>Kỹ năng ném shuriken</em></p>

👉 (Bạn nên chụp thêm ảnh gameplay thật để thay vào đây)

---
## 📂 4. Các bước cài đặt 

- Bước 1: Chuẩn bị môi trường

  - Trước khi chạy game, cần cài đặt các công cụ sau:

    - Python 3.12 trở lên

    - pip (trình quản lý thư viện Python)

- 👉 Kiểm tra Python đã cài chưa:

    - Chạy lệnh sau:

          python --version

- Bước 2: Tải mã nguồn

    - Clone project từ GitHub:

          git clone https://github.com/TruongDev10/HuyenThoaiNinja.git

    - Hoặc tải file .zip và giải nén.

- Bước 3: Di chuyển vào thư mục project

    - Chạy lệnh sau:

          cd HuyenThoaiNinja

- Bước 4: Tạo môi trường ảo (khuyến khích)

    - 👉 Giúp tránh lỗi xung đột thư viện

          python -m venv venv

- Kích hoạt môi trường:

  - Windows:

          venv\Scripts\activate
    
  - Mac/Linux:
    
          source venv/bin/activate

- Bước 5: Cài đặt thư viện

  - Cài các thư viện cần thiết:

          pip install pygame opencv-python mediapipe numpy

  - 👉 Nếu project có file requirements.txt:

          pip install -r requirements.txt

- Bước 6: Chạy game

    - Mở terminal và chạy lệnh sau: 

          python main.py


## 🧑‍💻 5. Người thực hiện

- **Bùi Văn Trường**
- GitHub: https://github.com/TruongDev10  

© 2026 - Faculty of Information Technology, DaiNam University