# 16:17 — Монгол төрийн түүхэн эргэлт

A Grade 10 Mongolian history short documentary (≈4 min, 1920×1080, 24 fps, Mongolian narration),
built as a **scripted Blender (bpy) + FFmpeg** project. The director pack (storyboard, narration,
fact-check, pipeline, art direction) lives in [`docs/director_pack/`](docs/director_pack/).
Project rules are in [`CLAUDE.md`](CLAUDE.md).

## Status (final production)

| Item | State |
|---|---|
| Narration, all 8 scenes | **Done**: ElevenLabs Eleven v4, voice «Bilguun» (approved), `audio/narration/scene01–08.mp3`, verified with ffprobe, 169.97 s total, aligned with `scripts/narration.py` |
| Scene builders 01–08 + end credits | **Done**, timed to the measured narration (`config/final_cut.env`) |
| Original score + sound design | **Done**: `scripts/make_score.py` (score), SFX synthesised in `scripts/assemble_final.py` |
| Native 1080p / 24 fps render | **Running**: `scripts/render_final.sh` (resumable). Check progress with `scripts/render_progress.sh` |
| Final film | Assembled by `scripts/assemble_final.py` once every scene is complete, then checked by `scripts/qc_final.sh` |

## Final pipeline (one command per step)

```bash
python3 scripts/narration.py              # verify + align the 8 narration files
python3 scripts/make_score.py 250         # original score -> audio/music/score_ambient.wav
scripts/render_final.sh                   # native 1920x1080, 24 unique fps, all scenes (resumable)
scripts/render_progress.sh                # frames done per scene
python3 scripts/assemble_final.py         # -> output/final/16_17_Republic_Day_FINAL_1080p.mp4
scripts/qc_final.sh                       # -> output/final/QC_REPORT.txt + QC_contact_sheet.png
```

On a laptop with a GPU, `ENGINE=eevee scripts/render_final.sh` is much faster. On this build server
(4-core CPU, no GPU) the lean Cycles profile (`--fast-final`: 4 samples + OpenImageDenoise) takes
about 8–30 s per 1080p frame.

## Requirements (all free / open source)
- **Blender 4.2–4.5 LTS** (tested with 4.5.16), https://www.blender.org/
- **FFmpeg**, https://ffmpeg.org/
- Kdenlive (optional, for the final edit)
- Fonts are bundled in `assets/fonts/` (Noto, SIL OFL)

## Run Scene 01

From the project root:

```bash
# 1. review stills only (fast)
blender -b --factory-startup --python scripts/build_scene01.py -- --stills 1,48,96,133,192

# 2. full 540p preview + MP4 with scratch clock-tick audio
scripts/render_scene.sh 01

# 3. on a laptop with a GPU, use EEVEE (much faster than Cycles CPU)
scripts/render_scene.sh 01 preview eevee

# 4. stretch to the real narration length, final 1080p
DURATION=17 scripts/render_scene.sh 01 final eevee
```

Builder options (after `--`): `--quality preview|final`, `--engine cycles|eevee`,
`--duration SECONDS`, `--samples N`, `--stills 1,96,192`, `--render`, `--frames 1-96`,
`--manuscript-image PATH` (a rights-cleared scan replaces the abstract manuscript),
`--no-save`.

Every run regenerates `scenes/scene01.blend`. Open it in Blender to edit the shot by hand.
Frames go to `output/scene01_<quality>_frames/` and the MP4 to `output/scene01_<quality>.mp4`.

Render cost measured on this build machine (4-core CPU, no GPU, Cycles, 16 samples + OpenImageDenoise):
about 20 s per 540p frame, so about 1 hour for the 8 s preview. EEVEE on any discrete or integrated GPU is
far faster. Without a GPU, EEVEE falls back to software OpenGL, which is slower than Cycles.

## Layout
```
CLAUDE.md                 project rules (from the director pack + implementation notes)
ASSET_MANIFEST.md         every asset, its origin and license
config/shots.json         scene list and timings
docs/director_pack/       original brief (storyboard, narration, sources …)
docs/SCENE_PLAN.md        how scenes 02–08 will be built
docs/QC_CHECKLIST.md      self-check list + POC review log
scripts/lib/              reusable helpers (render setup, materials, props, textures, titles/compositor)
scripts/build_scene01.py  Scene 01 builder
scripts/render_scene.sh   build + render + encode one scene
scripts/encode.sh         PNG sequence -> MP4 (+ audio) + contact sheet
scenes/                   generated, editable .blend files
assets/                   fonts, generated textures, (future) archival/music/sfx with licenses
previews/                 small review renders kept in git
```
