"""Step 1: breath cuts + 9:16 face-centred crop + radio voice chain.

Usage: python3 scripts/prep.py <video> [--id NAME] [--thresh -36]

Writes public/<id>/:
  cut.mp4      9:16 native crop (no upscale), pauses removed, video only
  raw_cut.wav  cut audio before processing (used for transcription + checks)
  voice.wav    processed voice, loudnorm -14 LUFS / TP -1.5
  prep.json    segments (source in/out -> output time), crop box, stats
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
FPS = 30
SR = 48000

VOICE_CHAIN = ",".join([
    "highpass=f=65",
    "afftdn=nr=8:nf=-48:tn=1",
    "rubberband=pitch=0.965:formant=shifted:pitchq=quality",
    "acompressor=threshold=-24dB:ratio=3:attack=12:release=160:makeup=3:knee=6",
    "bass=g=4.5:f=110:w=0.8",
    "equalizer=f=400:t=q:w=1.2:g=-1.5",
    "equalizer=f=4200:t=q:w=1.2:g=-2",
    "deesser=i=0.45:m=0.5:f=0.5",
    "treble=g=-4.5:f=7000:w=0.6",
    "alimiter=limit=0.89:attack=4:release=80",
])


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
               "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)]).stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = map(int, s["r_frame_rate"].split("/"))
    return s["width"], s["height"], num / den, float(j["format"]["duration"])


def face_center_x(path, w, h):
    """Median face centre (px) from MediaPipe face detection, sampled every 0.5s."""
    from mediapipe import Image, ImageFormat
    from mediapipe.tasks.python import BaseOptions, vision

    det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=str(ROOT / "models" / "blaze_face_short_range.tflite")),
        min_detection_confidence=0.5))
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    step = max(1, int(fps / 2))
    xs, ys, i = [], [], 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % step == 0:
            _, frame = cap.retrieve()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = det.detect(Image(image_format=ImageFormat.SRGB, data=rgb))
            if res.detections:
                b = max(res.detections, key=lambda d: d.bounding_box.width).bounding_box
                xs.append(b.origin_x + b.width / 2)
                ys.append(b.origin_y + b.height / 2)
        i += 1
    cap.release()
    det.close()
    if not xs:
        print("! no face found, centring crop")
        return w / 2, h / 2
    return float(np.median(xs)), float(np.median(ys))


def detect_keeps(audio, thresh_db, min_pause=0.15, pad=0.04):
    """RMS 20ms windows, 3-frame smoothing, pauses >= min_pause below thresh are cut."""
    win = int(SR * 0.02)
    n = len(audio) // win
    rms = np.sqrt(np.mean(audio[:n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    rms = np.convolve(rms, np.ones(3) / 3, mode="same")
    db = 20 * np.log10(rms + 1e-12)
    loud = db > thresh_db
    # speech runs
    keeps, i = [], 0
    while i < n:
        if loud[i]:
            j = i
            while j < n and loud[j]:
                j += 1
            keeps.append([i * 0.02, j * 0.02])
            i = j
        else:
            i += 1
    if not keeps:
        raise SystemExit("no speech detected; try --thresh lower")
    # merge runs separated by pauses shorter than min_pause
    merged = [keeps[0]]
    for s, e in keeps[1:]:
        if s - merged[-1][1] < min_pause:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    # drop tiny blips (< 60ms) that are clicks/breaths
    merged = [k for k in merged if k[1] - k[0] >= 0.06]
    dur = len(audio) / SR
    fr = 1 / FPS
    out = []
    for s, e in merged:
        s = max(0.0, s - pad)
        e = min(dur, e + pad)
        s = np.floor(s / fr) * fr
        e = np.ceil(e / fr) * fr
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([round(s, 4), round(e, 4)])
    return out, db


def band_db(x, lo, hi):
    spec = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return 10 * np.log10(spec[(f >= lo) & (f < hi)].mean() + 1e-20)


def loudnorm_2pass(src, dst, I=-14, TP=-1.5, LRA=9):
    first = run(["ffmpeg", "-hide_banner", "-i", str(src), "-af",
                 f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"]).stderr
    m = json.loads(re.findall(r"\{[^{}]+\}", first)[-1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true,aresample={SR}")
    run(["ffmpeg", "-y", "-hide_banner", "-i", str(src), "-af", af, "-ar", str(SR), str(dst)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--id")
    ap.add_argument("--thresh", type=float, default=-36)
    a = ap.parse_args()
    src = Path(a.video).resolve()
    vid = a.id or re.sub(r"[^A-Za-z0-9_-]+", "-", src.stem).strip("-")
    out = ROOT / "public" / vid
    out.mkdir(parents=True, exist_ok=True)

    w, h, fps, dur = probe(src)
    print(f"source {w}x{h} @ {fps:.2f}fps, {dur:.2f}s")

    # --- audio + pause detection
    full = out / "_full.wav"
    run(["ffmpeg", "-y", "-hide_banner", "-i", str(src), "-vn", "-ac", "1", "-ar", str(SR), str(full)])
    audio, _ = sf.read(full)
    keeps, _ = detect_keeps(audio, a.thresh)
    kept = sum(e - s for s, e in keeps)
    print(f"{len(keeps)} segments, {dur:.2f}s -> {kept:.2f}s ({(kept / dur - 1) * 100:+.1f}%)")

    # --- 9:16 crop centred on the face, native resolution
    cx, cy = face_center_x(src, w, h)
    ch = h - (h % 2)
    cw = int(round(ch * 9 / 16)) // 2 * 2
    x0 = int(np.clip(cx - cw / 2, 0, w - cw)) // 2 * 2
    print(f"crop {cw}x{ch} at x={x0} (face x={cx:.0f})")
    if ch < 1920:
        print(f"! WARNING: crop height {ch}px < 1920 -> render will upscale x{1920 / ch:.2f} (blurry). Use the original 4K file.")

    # --- cut video + raw audio with 10ms fades per segment
    # video: one streaming select (no per-segment buffering, so 4K fits in memory)
    half = 0.5 / FPS
    expr = "+".join(f"between(t,{s - half:.4f},{e - half:.4f})" for s, e in keeps)
    graph = out / "_cut.ffgraph"
    graph.write_text(f"[0:v]fps={FPS},select='{expr}',setpts=N/{FPS}/TB,crop={cw}:{ch}:{x0}:0[vout]")
    run(["ffmpeg", "-y", "-hide_banner", "-i", str(src), "-filter_complex_script", str(graph),
         "-map", "[vout]", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-g", "15", "-an", str(out / "cut.mp4")])
    # audio: cut in numpy with 10ms fades on every segment edge
    fade = int(SR * 0.01)
    ramp = np.linspace(0, 1, fade)
    parts = []
    for s, e in keeps:
        seg = audio[int(round(s * SR)):int(round(e * SR))].copy()
        seg[:fade] *= ramp[:len(seg[:fade])]
        seg[-fade:] *= ramp[::-1][-len(seg[-fade:]):]
        parts.append(seg)
    sf.write(out / "raw_cut.wav", np.concatenate(parts), SR, subtype="PCM_24")

    # --- radio voice chain + 2-pass loudnorm
    chain = out / "_chain.wav"
    run(["ffmpeg", "-y", "-hide_banner", "-i", str(out / "raw_cut.wav"), "-af", VOICE_CHAIN, "-ar", str(SR), str(chain)])
    loudnorm_2pass(chain, out / "voice.wav")

    raw, _ = sf.read(out / "raw_cut.wav")
    pro, _ = sf.read(out / "voice.wav")
    # compare tonal balance after matching overall level
    lvl = band_db(pro, 100, 8000) - band_db(raw, 100, 8000)
    low = band_db(pro, 60, 200) - band_db(raw, 60, 200) - lvl
    high = band_db(pro, 5000, 12000) - band_db(raw, 5000, 12000) - lvl
    print(f"tone check (level-matched): 60-200Hz {low:+.1f} dB (target ~+5), 5-12kHz {high:+.1f} dB (target ~-5)")

    # output timeline of segments
    segs, t = [], 0.0
    for s, e in keeps:
        segs.append({"srcIn": s, "srcOut": e, "start": round(t, 4), "end": round(t + e - s, 4)})
        t += e - s
    cut_frames = int(run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", str(out / "cut.mp4")]).stdout.strip())
    info = {"id": vid, "source": str(src), "sourceSize": [w, h], "crop": {"x": x0, "w": cw, "h": ch},
            "face": {"x": cx - x0, "y": cy}, "durationIn": dur, "duration": round(t, 4),
            "durationInFrames": cut_frames, "segments": segs,
            "tone": {"low": round(low, 2), "high": round(high, 2)}}
    (out / "prep.json").write_text(json.dumps(info, indent=2))
    for f in (full, chain, graph):
        f.unlink(missing_ok=True)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
