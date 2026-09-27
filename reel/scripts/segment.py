"""Step 2: person/background separation -> public/<id>/person_alpha.webm (VP9 + alpha).

Usage: python3 scripts/segment.py <id>

MediaPipe selfie_multiclass_256x256, mask = 1 - background.
Analysis at 540x960, mask upscaled, guidedFilter(r=8, eps=1e-4) on the full
frame, tighten x1.6, dark-microphone fix, temporal smoothing 0.35 (top) -> 0.1 (bottom).
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from mediapipe import Image, ImageFormat
from mediapipe.tasks.python import BaseOptions, vision

ROOT = Path(__file__).resolve().parent.parent


def main(vid):
    d = ROOT / "public" / vid
    cap = cv2.VideoCapture(str(d / "cut.mp4"))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(ROOT / "models" / "selfie_multiclass_256x256.tflite")),
        output_confidence_masks=True, output_category_mask=False))

    enc = subprocess.Popen([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "16", "-b:v", "0",
        "-deadline", "good", "-cpu-used", "4", "-row-mt", "1", "-auto-alt-ref", "0",
        str(d / "person_alpha.webm")], stdin=subprocess.PIPE)

    # temporal smoothing weight per row: 0.35 at top -> 0.1 at bottom (fast hands)
    wrow = np.linspace(0.35, 0.1, h, dtype=np.float32)[:, None]
    # microphone zone: lower-middle of the frame
    mic = np.zeros((h, w), bool)
    mic[int(h * 0.55):, int(w * 0.2):int(w * 0.8)] = True

    prev = None
    i = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        small = cv2.resize(rgb, (540, 960), interpolation=cv2.INTER_AREA if h > 960 else cv2.INTER_LINEAR)
        res = seg.segment(Image(image_format=ImageFormat.SRGB, data=np.ascontiguousarray(small)))
        bg = res.confidence_masks[0].numpy_view().astype(np.float32)
        a = 1.0 - bg
        a = cv2.resize(a, (w, h), interpolation=cv2.INTER_LINEAR)
        guide = rgb.astype(np.float32) / 255.0
        a = cv2.ximgproc.guidedFilter(guide, a, 8, 1e-4)
        a = np.clip((a - 0.5) * 1.6 + 0.5, 0, 1)
        dark = rgb.max(axis=2) < 70
        a[mic & dark] = 1.0
        if prev is not None:
            a = wrow * prev + (1 - wrow) * a
        prev = a
        rgba = np.dstack([rgb, (a * 255).astype(np.uint8)])
        enc.stdin.write(rgba.tobytes())
        i += 1
        if i % 300 == 0:
            print(f"  {i}/{total}")
    cap.release()
    seg.close()
    enc.stdin.close()
    enc.wait()
    print(f"-> {d / 'person_alpha.webm'} ({i} frames)")


if __name__ == "__main__":
    main(sys.argv[1])
