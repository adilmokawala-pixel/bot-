"""Step 4: build public/<id>/timeline.json (scenes, camera, captions, SFX).

Usage: python3 scripts/plan.py <id>

Inputs : prep.json, words.json (optional), edit.json (optional, hand-written)
edit.json lets a human/Claude add the editorial layer without touching code:
{
  "en":          {"<sentence index>": "ENGLISH LINE WITH «KEYWORD»"},
  "scenes":      {"<scene index>": {"keyword": "MRE", "icons": ["💰"], "path": ["الفكرة","الملف"]}},
  "pushes":      [<sentence index>, ...]           # force a persuasion push
  "noPush":      [<sentence index>, ...],
  "annotations": [{"type": "chip", "atWord": 12, "dur": 1.6, "text": "التمويل", "emoji": "💰"}, ...],
  "broll":       [{"atWord": 98, "untilWord": 124, "bg": "steps",
                   "steps": [{"atWord": 99, "emoji": "1️⃣", "title": "...", "sub": "..."}]}, ...]
}
"broll" = full-screen graphic without the person (voice and captions go on). It replaces the auto scenes
it overlaps. Any scene (auto or broll) can also take "noPerson": true, e.g. an "image" scene showing a chart.
annotation times: "atWord" (word index) or "at" (seconds); "untilWord" or "dur" for the end.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FPS = 30
SCENE_LEN = 4.0
CYCLE = ["original", "orange", "dark", "light"]
SFX_FOR = {"card": ("shimmer", 0.20), "chip": ("pop", 0.26), "chips2": ("pop", 0.24), "tiles": ("pop", 0.28), "dm": ("notif", 0.30), "cta": ("impact", 0.40)}


def sentences_from(words, segments):
    """Split words into sentences at cut points, long gaps or final punctuation."""
    cuts = {round(s["start"], 3) for s in segments[1:]}
    out, cur = [], []
    for i, w in enumerate(words):
        if cur:
            prev = words[cur[-1]]
            gap = w["start"] - prev["end"]
            crossed = any(prev["end"] - 0.05 <= c <= w["start"] + 0.05 for c in cuts)
            if gap > 0.35 or prev["w"][-1:] in ".?!؟،," or (crossed and len(cur) >= 3):
                out.append(cur)
                cur = []
        cur.append(i)
    if cur:
        out.append(cur)
    return out


def main(vid):
    d = ROOT / "public" / vid
    prep = json.loads((d / "prep.json").read_text())
    words = json.loads((d / "words.json").read_text()) if (d / "words.json").exists() else []
    edit = json.loads((d / "edit.json").read_text()) if (d / "edit.json").exists() else {}
    dur = prep["durationInFrames"] / FPS
    segments = [{"start": s["start"], "end": s["end"]} for s in prep["segments"]]

    # sentences: from words, or from segments when there is no transcript yet
    if words:
        sents = sentences_from(words, segments)
        sent_spans = [(words[s[0]]["start"], words[s[-1]]["end"]) for s in sents]
    else:
        sents = [[] for _ in segments]
        sent_spans = [(s["start"], s["end"]) for s in segments]

    # scenes: ~4s, snapped to the nearest sentence boundary
    bounds = sorted({round(b, 3) for sp in sent_spans for b in sp[:1]} | {s["start"] for s in segments})
    scene_starts, target = [0.0], SCENE_LEN
    while target < dur - 2.0:
        cand = [b for b in bounds if scene_starts[-1] + 2.5 <= b <= dur - 2.0]
        if not cand:
            break
        b = min(cand, key=lambda x: abs(x - target))
        scene_starts.append(b)
        target = b + SCENE_LEN
    scenes = []
    for i, st in enumerate(scene_starts):
        en = scene_starts[i + 1] if i + 1 < len(scene_starts) else dur
        sc = {"start": round(st, 3), "end": round(en, 3), "bg": CYCLE[i % 4]}
        sc.update(edit.get("scenes", {}).get(str(i), {}))  # may override bg, e.g. {"bg": "image", "image": "adil/img/bank.jpg"}
        scenes.append(sc)

    # b-roll: full-screen scenes without the person, carved into the auto scenes
    def word_time(a, key_word, key_sec, end=False):
        if key_word in a:
            return words[a[key_word]]["end" if end else "start"]
        return a.get(key_sec)

    for b in edit.get("broll", []):
        b = dict(b)
        st, en = word_time(b, "atWord", "at"), word_time(b, "untilWord", "until", end=True)
        for k in ("atWord", "at", "untilWord", "until"):
            b.pop(k, None)
        b["steps"] = [{**{k: v for k, v in s.items() if k != "atWord"}, "at": word_time(s, "atWord", "at")} for s in b.get("steps", [])]
        kept = []
        for sc in scenes:
            if sc["end"] <= st or sc["start"] >= en:
                kept.append(sc)
                continue
            if st - sc["start"] >= 1.5:
                kept.append({**sc, "end": round(st, 3)})
            if sc["end"] - en >= 1.5:
                kept.append({**sc, "start": round(en, 3)})
        kept.append({"start": round(st, 3), "end": round(en, 3), "bg": "image", **b, "noPerson": True})
        kept.sort(key=lambda x: x["start"])
        # close the gaps left by dropped slivers
        for i in range(len(kept) - 1):
            kept[i]["end"] = kept[i + 1]["start"]
        kept[0]["start"], kept[-1]["end"] = 0.0, round(dur, 3)
        scenes = kept

    # persuasion pushes: long sentences (>=5 words, >=2s) or spanning several segments
    pushes = []
    forced = set(edit.get("pushes", []))
    banned = set(edit.get("noPush", []))
    for i, (st, en) in enumerate(sent_spans):
        n_words = len(sents[i])
        n_segs = sum(1 for s in segments if s["start"] < en and s["end"] > st)
        auto = (n_words >= 5 and en - st >= 2.0) or n_segs >= 2
        if (auto or i in forced) and i not in banned and en - st >= 1.2:
            pushes.append({"start": round(st, 3), "end": round(en + 0.1, 3)})

    # caption groups: max 3 words, inside one sentence
    en_lines = edit.get("en", {})
    captions = []
    for si, s in enumerate(sents):
        for k in range(0, len(s), 3):
            idx = s[k:k + 3]
            captions.append({"words": idx, "start": words[idx[0]]["start"], "end": words[idx[-1]]["end"], "en": en_lines.get(str(si), "")})
    for i, c in enumerate(captions):
        nxt = captions[i + 1]["start"] if i + 1 < len(captions) else dur
        c["end"] = round(min(nxt, c["end"] + 0.6), 3)

    # annotations (editorial)
    def at(a, key_word, key_sec, default=None):
        if key_word in a:
            return words[a[key_word]]["start"]
        return a.get(key_sec, default)

    annotations = []
    for a in edit.get("annotations", []):
        a = dict(a)
        st = at(a, "atWord", "at")
        en = at(a, "untilWord", "until") or st + a.get("dur", 1.6)
        if a["type"] == "comment":
            a["typeStart"] = at(a, "typeWord", "typeStart", st + 0.3)
            a["typeEnd"] = a["typeStart"] + a.get("typeDur", 0.9)
        for k in ("atWord", "at", "untilWord", "until", "dur", "typeWord", "typeDur"):
            a.pop(k, None)
        a.update({"start": round(st, 3), "end": round(en, 3)})
        annotations.append(a)

    # SFX, tied to events
    sfx = []
    scene_cut = {sc["start"] for sc in scenes[1:]}
    for sc in scenes[1:]:
        sfx.append({"name": "whoosh", "at": round(sc["start"] - 0.2, 3), "volume": 0.32})
        if sc["bg"] in ("light", "image", "steps"):
            sfx.append({"name": "shimmer", "at": round(sc["start"] + 0.15, 3), "volume": 0.20})
    for s in segments[1:]:
        if all(abs(s["start"] - c) > 0.3 for c in scene_cut):
            sfx.append({"name": "swipe", "at": round(s["start"] - 0.06, 3), "volume": 0.16})
    for p in pushes:
        sfx.append({"name": "swell", "at": p["start"], "volume": 0.13})
        sfx.append({"name": "air", "at": round(p["end"] - 0.4, 3), "volume": 0.16})
    for a in annotations:
        if a["type"] in SFX_FOR:
            name, vol = SFX_FOR[a["type"]]
            sfx.append({"name": name, "at": a["start"], "volume": vol})
        elif a["type"] == "checklist":
            for k in range(len(a["items"])):
                sfx.append({"name": "check", "at": round(a["start"] + 0.25 * k, 3), "volume": 0.23})
        elif a["type"] == "comment":
            sfx.append({"name": "typing", "at": a["typeStart"], "volume": 0.34})
    sfx = sorted([s for s in sfx if 0 <= s["at"] < dur], key=lambda s: s["at"])

    tl = {
        "id": vid, "fps": FPS, "durationInFrames": prep["durationInFrames"],
        "video": {"src": f"{vid}/cut.mp4", "alpha": f"{vid}/person_alpha.webm",
                  "width": prep["crop"]["w"], "height": prep["crop"]["h"]},
        "voice": f"{vid}/voice.wav", "segments": segments,
        "words": [{"w": w["w"], "start": w["start"], "end": w["end"]} for w in words],
        "captions": captions, "scenes": scenes, "pushes": pushes, "annotations": annotations,
        "sfx": sfx, "music": {"src": "sfx/music.wav", "volume": 0.075},
    }
    (d / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
    print(f"{len(scenes)} scenes, {len(pushes)} pushes, {len(captions)} caption groups, "
          f"{len(annotations)} annotations, {len(sfx)} sfx -> {d / 'timeline.json'}")
    for i, (st, en) in enumerate(sent_spans):
        text = " ".join(words[k]["w"] for k in sents[i]) if words else ""
        print(f"  [{i}] {st:6.2f}-{en:6.2f}  {text}")


if __name__ == "__main__":
    main(sys.argv[1])
