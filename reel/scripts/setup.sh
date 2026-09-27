#!/bin/bash
# Installs every tool the reel pipeline needs. Idempotent; safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

export DEBIAN_FRONTEND=noninteractive
need_apt=()
command -v ffmpeg >/dev/null || need_apt+=(ffmpeg)
command -v rubberband >/dev/null || need_apt+=(rubberband-cli)
ldconfig -p | grep -q libEGL.so.1 || need_apt+=(libegl1 libgles2 libgl1)
if [ ${#need_apt[@]} -gt 0 ]; then
  apt-get update -qq || true
  apt-get install -y -qq --fix-missing "${need_apt[@]}" >/dev/null || apt-get install -y -qq --fix-missing --no-install-recommends "${need_apt[@]}" >/dev/null
fi

python3 -c "import faster_whisper, mediapipe, cv2, soundfile, pyloudnorm, scipy; cv2.ximgproc" 2>/dev/null \
  || pip install -q --root-user-action=ignore -r requirements.txt

mkdir -p models
MP=https://storage.googleapis.com/mediapipe-models
[ -s models/selfie_multiclass_256x256.tflite ] || curl -sSfL --retry 3 -o models/selfie_multiclass_256x256.tflite \
  "$MP/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite"
[ -s models/blaze_face_short_range.tflite ] || curl -sSfL --retry 3 -o models/blaze_face_short_range.tflite \
  "$MP/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"

[ -d node_modules/remotion ] || npm install --no-audit --no-fund --silent
[ -s public/sfx/music.wav ] || python3 scripts/sfx.py >/dev/null

# Whisper model: huggingface.co may be blocked by the network policy; don't fail the session for it.
python3 - 2>/dev/null <<'PY' || echo "reel setup: Whisper model not cached (huggingface.co blocked?) - transcription unavailable" >&2
import os
from faster_whisper import WhisperModel
WhisperModel(os.environ.get("WHISPER_MODEL", "large-v3-turbo"), device="cpu", compute_type="int8")
PY
echo "reel setup: ok"
