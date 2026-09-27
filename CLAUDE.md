# Mokawala Reel toolkit

This repo turns a raw talking-head video of Adil Meftah (Mokawala.ma, Moroccan Darija)
into a vertical 9:16 Reel in a fixed brand style. The full style spec is `reel/STYLE.md`;
follow it exactly and change only the content per video.

Tools are installed by `.claude/hooks/session-start.sh` → `reel/scripts/setup.sh`.

## Getting the video
Raw videos are uploaded by the user as assets of the GitHub release `videos`
(https://github.com/adilmokawala-pixel/bot-/releases/tag/videos) and downloaded into `videos/`
(git-ignored). Chat attachments are limited to 30 MB, so large files always go through the release.

## Pipeline (run from `reel/`)
1. `python3 scripts/prep.py ../videos/<file> --id <id>`: breath cuts, 9:16 face crop (native, no upscale), radio voice chain, loudnorm
2. `python3 scripts/segment.py <id>`: person alpha, written to `public/<id>/person_alpha.webm`
3. `python3 scripts/transcribe.py <id> [--text darija.txt]`: word timings (needs huggingface.co allowed)
4. Write `public/<id>/edit.json` by hand: English lines, scene keywords/icons/path/images, annotations, forced pushes (format in `scripts/plan.py` docstring)
5. `python3 scripts/plan.py <id>`: builds `public/<id>/timeline.json` (scenes every ~4s, zooms, captions, SFX)
6. `python3 scripts/render.py <id> [--frames 0-149]`: Remotion render + mastering + checks, writes `out/<id>-Reel-9x16.mp4` and `out/<id>-contact.jpg`

Before delivering, look at the contact sheet: captions inside the frame and below the mouth, Arabic not clipped,
emoji visible, clean person edges on replaced backgrounds. Report every Darija correction and every added
fact to the user for approval. Never invent content the speaker didn't say.

## Library
- `reel/src/`: Remotion components (`Reel.tsx` camera/scenes/transitions/audio, `Captions.tsx`, `Annotations.tsx`, `Backgrounds.tsx`, `Glass.tsx`, `brand.ts`)
- `reel/darija/corrections.json`: Whisper → Darija fixes; extend it after every video the user reviews
- `reel/public/sfx/`: procedurally generated SFX + music (`scripts/sfx.py`)
- `reel/public/fonts/`: drop `ThmanyahSans-Bold.woff2|ttf|otf` here (not redistributable, falls back to Cairo)
