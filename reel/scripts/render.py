"""Step 5: render with Remotion, master the mix, run the pre-delivery checks.

Usage: python3 scripts/render.py <id> [--frames 0-89]

-> out/<id>-Reel-9x16.mp4  (1080x1920, 30fps, H.264 CRF16, AAC 320k, -14 LUFS, TP <= -1)
-> out/<id>-contact.jpg    (~10 frames: every scene, every push, the ending)
"""
import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BROWSERS = [
    os.environ.get("REMOTION_BROWSER", ""),
    "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
]


def run(cmd, **kw):
    print("$", " ".join(map(str, cmd))[:200])
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def loudness(path):
    err = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
               "-f", "null", "-"]).stderr
    return json.loads(re.findall(r"\{[^{}]+\}", err)[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--frames", help="render only a frame range, e.g. 0-89 (preview)")
    a = ap.parse_args()
    vid = a.id
    tl = json.loads((ROOT / "public" / vid / "timeline.json").read_text())
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    raw = out_dir / f"{vid}-raw.mp4"
    final = out_dir / f"{vid}-Reel-9x16.mp4"

    cmd = ["npx", "remotion", "render", "Reel", str(raw), f"--props={json.dumps({'id': vid})}",
           "--codec=h264", "--crf=16", "--audio-bitrate=320k", "--audio-codec=aac", "--concurrency=4",
           "--timeout=120000"]
    browser = next((b for b in BROWSERS if b and Path(b).exists()), None)
    if browser:
        cmd.append(f"--browser-executable={browser}")
    if a.frames:
        cmd.append(f"--frames={a.frames}")
    subprocess.run(cmd, check=True, cwd=ROOT)

    # master: 2-pass loudnorm on the full mix -> -14 LUFS, TP -1.5 (so the peak stays <= -1 dBFS)
    m = loudness(raw)
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
          f":linear=true,aresample=48000")
    run(["ffmpeg", "-y", "-hide_banner", "-i", str(raw), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
         "-af", af, "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", str(final)])
    raw.unlink()

    # checks
    p = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_name,width,height,r_frame_rate,nb_frames,bit_rate", "-of", "json", str(final)]).stdout)
    v = next(s for s in p["streams"] if s["codec_name"] == "h264")
    fin = loudness(final)
    frames_ok = a.frames or int(v["nb_frames"]) == tl["durationInFrames"]
    print("\nCHECKS")
    print(f"  size      {v['width']}x{v['height']} @ {v['r_frame_rate']}  frames {v['nb_frames']} / {tl['durationInFrames']}  {'OK' if frames_ok else 'MISMATCH'}")
    print(f"  loudness  {fin['input_i']} LUFS (target -14)   true peak {fin['input_tp']} dBTP (<= -1)")

    # contact sheet: each scene start, each push peak, the end
    times = [sc["start"] + 0.5 for sc in tl["scenes"]] + [p["end"] - 0.5 for p in tl["pushes"]]
    times.append(tl["durationInFrames"] / tl["fps"] - 0.2)
    times = sorted(set(round(t, 2) for t in times))
    if len(times) > 12:
        step = len(times) / 12
        times = [times[int(i * step)] for i in range(12)] + [times[-1]]
    if a.frames:
        lo, hi = (int(x) / tl["fps"] for x in a.frames.split("-"))
        times = [t - lo for t in times if lo <= t <= hi] or [0]
    tmp = out_dir / "_cs"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    for i, t in enumerate(times):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(final), "-frames:v", "1",
                        "-vf", f"scale=360:640,drawtext=text='{t:.1f}s':x=10:y=10:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.5",
                        str(tmp / f"{i:02d}.jpg")], check=True)
    cols = min(5, len(times))
    rows = -(-len(times) // cols)
    run(["ffmpeg", "-y", "-v", "error", "-framerate", "1", "-i", str(tmp / "%02d.jpg"), "-vf", f"tile={cols}x{rows}",
         "-frames:v", "1", str(out_dir / f"{vid}-contact.jpg")])
    shutil.rmtree(tmp)
    print(f"\n-> {final}\n-> {out_dir / f'{vid}-contact.jpg'}")


if __name__ == "__main__":
    main()
