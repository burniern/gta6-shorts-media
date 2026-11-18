#!/usr/bin/env python3
"""Mesure le mouvement de chaque clip (broll/ et broll/faces/) -> broll/MOTION.json.
Score = différence moyenne entre images successives (0-255). Plus c'est haut, plus ça bouge."""
import glob, json, os, subprocess
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "broll", "MOTION.json")
scores = json.load(open(OUT)) if os.path.exists(OUT) else {}
for p in sorted(glob.glob(os.path.join(HERE, "broll", "*.mp4")) + glob.glob(os.path.join(HERE, "broll", "faces", "*.mp4"))):
    k = os.path.relpath(p, os.path.join(HERE, "broll"))
    if k in scores:
        continue
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "1", "-i", p, "-t", "6", "-vf", "fps=6,scale=90:160,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8)
    if a.size < 2 * 90 * 160:
        continue
    a = a[: a.size // (90 * 160) * 90 * 160].reshape(-1, 160, 90).astype(np.float32)
    scores[k] = round(float(np.abs(np.diff(a, axis=0)).mean()), 2)
    print(k, scores[k])
json.dump(scores, open(OUT, "w"), indent=0)
