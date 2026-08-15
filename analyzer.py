"""
analyzer.py
------------
TrackPulse core engine.

This is a hybrid computer-vision + rule-based classifier (not a pretrained
"call one API" solution, and not a from-scratch deep net either — a balanced
middle ground that's perfect for a hackathon timeline):

1. Extract handcrafted visual features from each frame using OpenCV:
   - brightness (mean V channel)
   - saturation (mean S channel)
   - specular highlight ratio (bright, low-saturation pixels -> glare from
     a wet/reflective surface)
   - edge density (Canny edges -> dry tarmac is "textured/grainy", wet
     tarmac looks smoother/blurrier because reflections wash out texture)

2. Combine these into a single 0-100 "wetness score" using weighted rules.

3. Map the score to a label (Dry / Damp / Wet).

4. Look at the last few readings (the "history window") to decide if the
   track is trending drier -> overrides the label to "Drying" and drives
   the tire-change suggestion engine.
"""

import cv2
import numpy as np


class TrackConditionAnalyzer:
    def __init__(self, drying_delta: float = 8.0, history_window: int = 3):
        """
        drying_delta:   how much the wetness score has to drop (vs the
                         recent average) before we call it "Drying".
        history_window: how many previous frames count as "recent".
        """
        self.drying_delta = drying_delta
        self.history_window = history_window

    # ---------- 1. feature extraction ----------
    def extract_features(self, img_bgr: np.ndarray) -> dict:
        img = cv2.resize(img_bgr, (320, 240))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        brightness = float(np.mean(v))
        saturation = float(np.mean(s))

        # glare / specular highlight: very bright + washed-out (low sat) pixels
        highlight_mask = (v > 235) & (s < 40)
        specular_ratio = float(np.sum(highlight_mask)) / highlight_mask.size

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0)) / edges.size

        return {
            "brightness": brightness,
            "saturation": saturation,
            "specular_ratio": specular_ratio,
            "edge_density": edge_density,
        }

    # ---------- 2. wetness score ----------
    def compute_wetness_score(self, feats: dict) -> float:
        specular_norm = min(feats["specular_ratio"] * 8, 1.0)
        edge_norm = min(feats["edge_density"] * 4, 1.0)
        darkness_norm = 1 - min(feats["brightness"] / 255, 1.0)

        score = (
            0.45 * specular_norm
            + 0.35 * (1 - edge_norm)
            + 0.20 * darkness_norm
        ) * 100
        return round(min(max(score, 0), 100), 1)

    # ---------- 3. base label ----------
    def base_label(self, score: float) -> str:
        if score < 28:
            return "Dry"
        elif score < 52:
            return "Damp"
        else:
            return "Wet"

    # ---------- 4. full classification w/ trend awareness ----------
    def classify(self, img_bgr: np.ndarray, history: list | None = None) -> dict:
        feats = self.extract_features(img_bgr)
        score = self.compute_wetness_score(feats)
        label = self.base_label(score)
        trend = "steady"

        if history:
            recent = [h["score"] for h in history[-self.history_window:]]
            avg_recent = sum(recent) / len(recent)
            delta = score - avg_recent

            if delta <= -self.drying_delta and label != "Dry":
                label = "Drying"
                trend = "improving"
            elif delta <= -self.drying_delta / 2:
                trend = "improving"
            elif delta >= self.drying_delta / 2:
                trend = "worsening"

        return {"label": label, "score": score, "features": feats, "trend": trend}

    # ---------- 5. suggestion engine ----------
    def suggestion(self, current: dict) -> str:
        label, trend = current["label"], current["trend"]

        if label == "Dry" and trend != "worsening":
            return "✅ Track is dry and stable — slicks are good to go."
        if label == "Drying":
            return "🔄 Track is drying out. Tire change window approaching — get ready to switch to slicks/inters."
        if label == "Damp":
            if trend == "worsening":
                return "⚠️ Damp and getting wetter — consider switching to intermediates soon."
            return "🟡 Track is damp. Monitor closely before committing to slicks."
        if label == "Wet":
            if trend == "improving":
                return "🔵 Wet but conditions are improving — hold current tires, watch for the drying trend."
            return "🌧️ Track is wet — full wets/intermediates recommended."
        return "Monitoring track conditions..."
