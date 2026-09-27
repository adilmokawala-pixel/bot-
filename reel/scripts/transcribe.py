"""Step 3: word-level transcription (faster-whisper large-v3-turbo) + Darija fixes.

Usage: python3 scripts/transcribe.py <id> [--text correct_darija.txt] [--prompt "Darija context sentence"]

Reads public/<id>/raw_cut.wav (already cut, so times match the reel timeline).
Writes public/<id>/words.json and prints:
  - every automatic Darija correction (from darija/corrections.json)
  - low-confidence words to review
If --text is given, the user's exact wording replaces Whisper's words and only
Whisper's timings are kept (aligned with difflib).
"""
import argparse
import difflib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("WHISPER_MODEL", "large-v3-turbo")
INITIAL_PROMPT = (
    "فيديو بالدارجة المغربية على المقاولة والتمويل: الدعم، القرض، الملف، البنك، المشروع، "
    "مغاربة العالم MRE، فرصة، انطلاقة، تمويل، ديالك، كيفاش، فالبلاد، فالتعليق، شنو، بزاف."
)
AR_DIACRITICS = re.compile(r"[ً-ْـ]")


def norm(w):
    w = AR_DIACRITICS.sub("", w)
    w = re.sub(r"[^\w؀-ۿ]", "", w)
    return w.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي").lower()


def load_corrections():
    p = ROOT / "darija" / "corrections.json"
    return json.loads(p.read_text()) if p.exists() else {}


def whisper_words(wav, prompt=INITIAL_PROMPT):
    from faster_whisper import WhisperModel

    try:
        model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    except Exception as e:  # network policy blocks huggingface.co
        raise SystemExit(
            f"! cannot load Whisper model '{MODEL}': {e}\n"
            "  Allow huggingface.co + cdn-lfs.huggingface.co + cas-bridge.xethub.hf.co in the environment's "
            "network settings, or set WHISPER_MODEL to a local CTranslate2 model folder.")
    segs, _ = model.transcribe(str(wav), language="ar", word_timestamps=True, initial_prompt=prompt,
                               condition_on_previous_text=False, vad_filter=False, beam_size=5)
    out = []
    for s in segs:
        for w in s.words:
            t = w.word.strip()
            if t:
                out.append({"w": t, "start": round(w.start, 3), "end": round(w.end, 3), "p": round(w.probability, 3)})
    return out


def align_text(words, text):
    """Keep the user's words, borrow timings from Whisper."""
    user = text.split()
    a = [norm(w["w"]) for w in words]
    b = [norm(w) for w in user]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    times = [None] * len(user)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("equal", "replace") and i2 > i1:
            # spread whisper span [i1,i2) over user words [j1,j2)
            st, en = words[i1]["start"], words[i2 - 1]["end"]
            n = j2 - j1
            for k in range(n):
                times[j1 + k] = (st + (en - st) * k / n, st + (en - st) * (k + 1) / n)
    # fill gaps (inserted words) by interpolation
    for j in range(len(user)):
        if times[j] is None:
            prev = next((times[k][1] for k in range(j - 1, -1, -1) if times[k]), 0.0)
            nxt = next((times[k][0] for k in range(j + 1, len(user)) if times[k]), prev + 0.3)
            times[j] = (prev, max(prev + 0.08, min(nxt, prev + 0.35)))
    return [{"w": w, "start": round(s, 3), "end": round(e, 3), "p": 1.0} for w, (s, e) in zip(user, times)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--text", help="file with the exact Darija wording")
    ap.add_argument("--prompt", default=INITIAL_PROMPT,
                    help="Whisper initial prompt; a Darija sentence with the video's own terms keeps it from drifting to MSA")
    a = ap.parse_args()
    d = ROOT / "public" / a.id
    words = whisper_words(d / "raw_cut.wav", a.prompt)
    fixes = []
    if a.text:
        words = align_text(words, Path(a.text).read_text())
    else:
        corr = load_corrections()
        for w in words:
            key = AR_DIACRITICS.sub("", w["w"])
            if key in corr:
                fixes.append((w["w"], corr[key], w["start"]))
                w["orig"], w["w"] = w["w"], corr[key]
    (d / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
    print(" ".join(w["w"] for w in words))
    print(f"\n{len(words)} words -> {d / 'words.json'}")
    if fixes:
        print("\nauto-corrections:")
        for o, n, t in fixes:
            print(f"  {t:6.2f}s  {o} -> {n}")
    low = [w for w in words if w["p"] < 0.5]
    if low:
        print("\nlow confidence (review):")
        for w in low:
            print(f"  {w['start']:6.2f}s  {w['w']}  (p={w['p']})")


if __name__ == "__main__":
    main()
