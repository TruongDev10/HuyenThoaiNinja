import os
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_FILENAME = "hand_landmarker.task"


class HandTracker:
    def __init__(self):
        model_path = self._ensure_model()
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.7,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def _ensure_model(self):
        model_dir = os.path.join(os.path.dirname(__file__), os.pardir, "assets", "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, MODEL_FILENAME)
        if not os.path.exists(model_path):
            print("Dang tai mo hinh hand landmarker...")
            urllib.request.urlretrieve(MODEL_URL, model_path)
            print("Tai hoan tat.")
        return model_path

    def count_fingers(self, hand_landmarks):
        landmarks = hand_landmarks
        fingers = []
        fingers.append(1 if landmarks[4].x > landmarks[3].x else 0)
        tips_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]
        for tip, pip in zip(tips_ids, pip_ids):
            fingers.append(1 if landmarks[tip].y < landmarks[pip].y else 0)
        return sum(fingers)

    def get_hands_data(self, frame, width, height, draw=True):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detection_result = self.detector.detect(mp_image)
        hands_data = []
        if not detection_result.hand_landmarks:
            return hands_data

        for index, hand in enumerate(detection_result.hand_landmarks):
            x = int(hand[0].x * width)
            y = int(hand[0].y * height)
            label = "Unknown"
            if getattr(detection_result, "handedness", None) and index < len(detection_result.handedness):
                handedness = detection_result.handedness[index]
                if handedness:
                    detected_label = handedness[0].category_name
                    label = "Left" if detected_label == "Right" else "Right" if detected_label == "Left" else detected_label
            hands_data.append(
                {
                    "label": label,
                    "x": x,
                    "y": y,
                    "fingers": self.count_fingers(hand),
                    "landmarks": hand,
                }
            )

        if all(hand["label"] == "Unknown" for hand in hands_data):
            ordered = sorted(hands_data, key=lambda hand: hand["x"])
            if len(ordered) >= 1:
                ordered[0]["label"] = "Left"
            if len(ordered) >= 2:
                ordered[-1]["label"] = "Right"
            hands_data = ordered

        if draw:
            for hand in hands_data:
                color = (255, 200, 0) if hand["label"] == "Left" else (0, 255, 0)
                for landmark in hand["landmarks"]:
                    cx, cy = int(landmark.x * width), int(landmark.y * height)
                    cv2.circle(frame, (cx, cy), 3, color, -1)

        return hands_data

    def get_player_action(self, frame, width, height):
        hands = self.get_hands_data(frame, width, height, draw=True)
        if not hands:
            return False, width // 2, height // 2, 0

        preferred = None
        for hand in hands:
            if hand["label"] == "Right":
                preferred = hand
                break
        if preferred is None:
            preferred = max(hands, key=lambda hand: hand["x"])
        return True, preferred["x"], preferred["y"], preferred["fingers"]
