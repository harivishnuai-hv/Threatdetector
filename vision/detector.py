from __future__ import annotations
import cv2
from ultralytics import YOLO

MODEL_NAME = "yolov8n.pt"

def load_detector():
    """Load a small pretrained YOLO model; first use may download weights."""
    return YOLO(MODEL_NAME)

def detect_people(model, frame, confidence: float = 0.35):
    """Return person detections as (x1, y1, x2, y2, confidence)."""
    results = model.predict(frame, classes=[0], conf=confidence, imgsz=640, verbose=False)
    detections = []
    if not results:
        return detections
    boxes = results[0].boxes
    if boxes is None:
        return detections
    for box in boxes:
        coords = box.xyxy[0].cpu().numpy().tolist()
        conf = float(box.conf[0].cpu().item())
        detections.append((*[int(v) for v in coords], conf))
    return detections

def draw_detections(frame, detections):
    out = frame.copy()
    for x1, y1, x2, y2, conf in detections:
        cv2.rectangle(out, (x1, y1), (x2, y2), (40, 200, 80), 2)
        cv2.putText(out, f"Person {conf:.2f}", (x1, max(20, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 200, 80), 2)
    return out
