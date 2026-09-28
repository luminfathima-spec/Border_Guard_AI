import os
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from ultralytics import YOLO
from app.core.config import settings
from app.core.logging import logger

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

class YOLODetector:
    def __init__(self, model_path: Optional[str] = None, conf_threshold: Optional[float] = None):
        self.conf_threshold = conf_threshold or settings.CONFIDENCE_THRESHOLD
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Resolve model path
        raw_path = model_path or settings.YOLO_MODEL_PATH
        self.model_path = str(settings.get_absolute_path(raw_path))

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        logger.info(f"Initializing YOLOv8 detector on device '{self.device}' with model: {self.model_path}")
        try:
            # If local file doesn't exist yet, Ultralytics downloads yolov8n.pt automatically
            self.model = YOLO(self.model_path if os.path.exists(self.model_path) else "yolov8n.pt")
            if not os.path.exists(self.model_path):
                # Save downloaded weights to configured path
                self.model.save(self.model_path)
            logger.info(f"YOLOv8 model loaded successfully ({self.device}).")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise

    def detect_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs object detection on a single BGR OpenCV frame.
        Returns list of structured detections with normalized bounding boxes:
        [{'class_name': 'person', 'confidence': 0.89, 'bbox': [x1, y1, x2, y2], 'class_id': 0}]
        """
        height, width = frame.shape[:2]
        if height == 0 or width == 0:
            return []

        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            device=self.device,
            verbose=False,
        )

        detections = []
        if not results:
            return detections

        result = results[0]
        boxes = result.boxes

        if boxes is None:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            
            # Filter for surveillance-relevant classes
            if cls_id not in SURVEILLANCE_CLASSES:
                continue

            xyxy = box.xyxy[0].tolist() # [x1_px, y1_px, x2_px, y2_px]

            # Normalize coordinates to 0.0 - 1.0
            norm_bbox = [
                max(0.0, min(1.0, xyxy[0] / width)),
                max(0.0, min(1.0, xyxy[1] / height)),
                max(0.0, min(1.0, xyxy[2] / width)),
                max(0.0, min(1.0, xyxy[3] / height)),
            ]

            detections.append({
                "class_id": cls_id,
                "class_name": SURVEILLANCE_CLASSES.get(cls_id, f"obj_{cls_id}"),
                "confidence": round(conf, 4),
                "bbox": norm_bbox, # [x1, y1, x2, y2]
                "bbox_pixels": [int(v) for v in xyxy],
            })

        return detections
