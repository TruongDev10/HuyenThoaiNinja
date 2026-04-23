import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import urllib.request

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_FILENAME = "hand_landmarker.task"

class HandTracker:
    def __init__(self):
        model_path = self._ensure_model()
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.7
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def _ensure_model(self):
        model_dir = os.path.join(os.path.dirname(__file__), os.pardir, "assets", "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, MODEL_FILENAME)
        if not os.path.exists(model_path):
            print("Đang tải mô hình hand landmarker...")
            urllib.request.urlretrieve(MODEL_URL, model_path)
            print("Tải hoàn tất.")
        return model_path

    def count_fingers(self, hand_landmarks):
        landmarks = hand_landmarks
        fingers = []
        # Ngón cái
        if landmarks[4].x > landmarks[3].x:
            fingers.append(1)
        else:
            fingers.append(0)
        # 4 ngón còn lại
        tips_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]
        for tip, pip in zip(tips_ids, pip_ids):
            if landmarks[tip].y < landmarks[pip].y:
                fingers.append(1)
            else:
                fingers.append(0)
        return sum(fingers)

    def get_player_action(self, frame, width, height):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detection_result = self.detector.detect(mp_image)
        found = False
        x, y = width//2, height//2
        finger_count = 0
        if detection_result.hand_landmarks:
            hand = detection_result.hand_landmarks[0]
            x = int(hand[0].x * width)
            y = int(hand[0].y * height)
            finger_count = self.count_fingers(hand)
            found = True
            # Vẽ các điểm lên frame
            for landmark in hand:
                cx, cy = int(landmark.x * width), int(landmark.y * height)
                cv2.circle(frame, (cx, cy), 3, (0,255,0), -1)
        return found, x, y, finger_count