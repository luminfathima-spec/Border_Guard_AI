import os
import torch
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from ultralytics import YOLO
from app.core.config import settings
from app.core.logging import logger

# Strictly physical, objective object classes
SURVEILLANCE_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "airplane",
    5: "bus",
    6: "train",
    7: "truck",
    8: "boat",
    15: "bird",
    16: "cat",
    17: "dog",
    18: "horse",
    19: "sheep",
    20: "cow",
    21: "elephant",
    22: "bear",
    23: "zebra",
    24: "giraffe",
    26: "handbag",
    28: "suitcase",
}

HUMAN_CLASSES: Set[str] = {"person"}
VEHICLE_CLASSES: Set[str] = {"car", "truck", "bus", "motorcycle", "bicycle", "boat", "airplane", "train"}
ANIMAL_CLASSES: Set[str] = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}


class YOLODetector:
    """
    Local Edge Object Detector leveraging Ultralytics YOLOv8.

    SAFETY & ETHICS MANDATE:
    1. Do not infer hostility, nationality, criminality, or identity from visual appearance.
    2. Detection confidence reflects physical object presence likelihood, NOT malicious intent.
    3. Classification is restricted strictly to physical taxonomy (e.g., person, vehicle).
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        device: Optional[str] = None,
        target_resolution: Optional[Tuple[int, int]] = None,
    ):
        self.conf_threshold = conf_threshold or settings.CONFIDENCE_THRESHOLD
        
        # Support explicit CPU device override for local testing / dev
        if device:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.target_resolution = target_resolution  # (width, height) for inference scaling

        # Resolve model path
        raw_path = model_path or settings.YOLO_MODEL_PATH
        self.model_path = str(settings.get_absolute_path(raw_path))
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        logger.info(f"Initializing YOLOv8 detector on device '{self.device}' with model: {self.model_path}")
        try:
            self.model = YOLO(self.model_path if os.path.exists(self.model_path) else "yolov8n.pt")
            if not os.path.exists(self.model_path):
                self.model.save(self.model_path)
            logger.info(f"YOLOv8 model loaded successfully ({self.device}).")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise

    def detect_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs object detection on a single BGR OpenCV frame.
        Supports resolution downscaling for efficient CPU inference while projecting
        bounding box coordinates back to the original image dimensions.

        Returns list of structured detections:
        [
            {
                'class_id': 0,
                'class_name': 'person',
                'category': 'human', # 'human' | 'vehicle' | 'animal' | 'object'
                'confidence': 0.89,
                'bbox': [x1_norm, y1_norm, x2_norm, y2_norm],
                'bbox_pixels': [x1, y1, x2, y2]
            }
        ]
        """
        orig_height, orig_width = frame.shape[:2]
        if orig_height == 0 or orig_width == 0:
            return []

        # Optional inference scaling (e.g., downscale to 640 for rapid CPU processing)
        if self.target_resolution and (orig_width, orig_height) != self.target_resolution:
            infer_frame = cv2.resize(frame, self.target_resolution, interpolation=cv2.INTER_LINEAR)
        else:
            infer_frame = frame

        try:
            results = self.model.predict(
                source=infer_frame,
                conf=self.conf_threshold,
                device=self.device,
                verbose=False,
            )
        except Exception as e:
            logger.warning(f"Detection inference error on device {self.device}: {e}")
            return []

        detections = []
        if not results:
            return detections

        result = results[0]
        boxes = result.boxes
        if boxes is None:
            return detections

        infer_height, infer_width = infer_frame.shape[:2]
        scale_x = orig_width / float(infer_width)
        scale_y = orig_height / float(infer_height)

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())

            if cls_id not in SURVEILLANCE_CLASSES:
                continue

            class_name = SURVEILLANCE_CLASSES[cls_id]
            xyxy_infer = box.xyxy[0].tolist()

            # Map back to original frame coordinates
            x1 = max(0, min(orig_width, xyxy_infer[0] * scale_x))
            y1 = max(0, min(orig_height, xyxy_infer[1] * scale_y))
            x2 = max(0, min(orig_width, xyxy_infer[2] * scale_x))
            y2 = max(0, min(orig_height, xyxy_infer[3] * scale_y))

            # Normalized bounding box [0.0 - 1.0]
            norm_bbox = [
                round(x1 / orig_width, 4),
                round(y1 / orig_height, 4),
                round(x2 / orig_width, 4),
                round(y2 / orig_height, 4),
            ]

            # Categorize
            if class_name in HUMAN_CLASSES:
                category = "human"
            elif class_name in VEHICLE_CLASSES:
                category = "vehicle"
            elif class_name in ANIMAL_CLASSES:
                category = "animal"
            else:
                category = "object"

            detections.append({
                "class_id": cls_id,
                "class_name": class_name,
                "category": category,
                "confidence": round(conf, 4),
                "bbox": norm_bbox,
                "bbox_pixels": [int(x1), int(y1), int(x2), int(y2)],
            })

        return detections
