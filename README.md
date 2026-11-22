# 16:17 — Монгол төрийн түүхэн эргэлт

A Grade 10 Mongolian history short documentary (≈4 min, 1920×1080, 24 fps, Mongolian narration),
built as a **scripted Blender (bpy) + FFmpeg** project. The director pack (storyboard, narration,
fact-check, pipeline, art direction) lives in [`docs/director_pack/`](docs/director_pack/).
Project rules are in [`CLAUDE.md`](CLAUDE.md).

## Status

| Stage | State |
|---|---|
| Scene 01 POC: 8 s, 3D manuscript, moving camera, dynamic light/shadows, dust, clock reaching 16:17, Mongolian title | **Done**: rendered at 960×540 and reviewed frame by frame (see `docs/QC_CHECKLIST.md`) |
| Scene 01 at full VO length (~17 s) and 1080p | Ready to render: `DURATION=17 scripts/render_scene.sh 01 final` |
| Scenes 02–08 | Planned in [`docs/SCENE_PLAN.md`](docs/SCENE_PLAN.md); not built yet |
| Narration WAVs, music, SRT, final assembly | Not started |

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
