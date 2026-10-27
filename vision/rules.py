from __future__ import annotations
import cv2
import numpy as np

class MotionRuleEngine:
    """Unvalidated heuristic for generating a possible-altercation review cue.

    This is deliberately not presented as a fight classifier. It combines a
    close pair of person detections with frame-to-frame motion in their shared
    image region and requires the cue to persist across multiple updates.
    """
    def __init__(self, motion_threshold: float = 13.0, required_streak: int = 3):
        self.previous_gray = None
        self.streak = 0
        self.motion_threshold = motion_threshold
        self.required_streak = required_streak

    def update(self, frame, detections):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]
        boxes = []
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det[:4]]
            x1, x2 = max(0, x1), min(w - 1, x2)
            y1, y2 = max(0, y1), min(h - 1, y2)
            if x2 > x1 and y2 > y1:
                boxes.append((x1, y1, x2, y2))
        close_pair = False
        motion_score = 0.0
        if self.previous_gray is not None:
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    a, b = boxes[i], boxes[j]
                    acx, acy = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
                    bcx, bcy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                    ah, bh = a[3] - a[1], b[3] - b[1]
                    dist = ((acx - bcx) ** 2 + (acy - bcy) ** 2) ** 0.5
                    if dist < 0.9 * max(ah, bh):
                        close_pair = True
                        x1 = max(0, min(a[0], b[0]) - 12)
                        y1 = max(0, min(a[1], b[1]) - 12)
                        x2 = min(w, max(a[2], b[2]) + 12)
                        y2 = min(h, max(a[3], b[3]) + 12)
                        old = self.previous_gray[y1:y2, x1:x2]
                        new = gray[y1:y2, x1:x2]
                        if old.size and old.shape == new.shape:
                            motion_score = max(motion_score, float(np.mean(cv2.absdiff(old, new))))
        candidate = close_pair and motion_score >= self.motion_threshold
        self.streak = self.streak + 1 if candidate else 0
        cue = self.streak >= self.required_streak
        self.previous_gray = gray
        cues = ["Close pair + sustained visual motion (heuristic)"] if cue else []
        return cues, {"close_pair": close_pair, "motion_score": motion_score, "streak": self.streak}
