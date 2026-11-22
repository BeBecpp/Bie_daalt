# Technical Production Pipeline — Open Source First

### Minimum stack
- Claude Code in project directory (AI-assisted coding; Claude service itself is not open-source).
- Blender (GPL, free/open-source): bpy scene generation, moving camera/lights, EEVEE render, 3D layers, keyframes. https://www.blender.org/
- Kdenlive (GPL, free/open-source): edit, audio balance, titles/subtitles, output. https://kdenlive.org/
- FFmpeg (open-source): PNG sequences to MP4, audio merging. https://ffmpeg.org/
- Krita or GIMP + Inkscape: archival still layer extraction and titles.
- Noto fonts (SIL OFL): labels and subtitle.
- ElevenLabs Eleven v4 (Mongolian `mn` is officially supported) as an optional closed paid TTS: https://elevenlabs.io/docs/overview/models/
- Fallback Mongolian TTS: `facebook/mms-tts-mon` model has weights available but **CC-BY-NC-4.0** restriction, not OSI open-source; suitable only if that license covers this noncommercial school project: https://huggingface.co/facebook/mms-tts-mon

### Project layout expected after Claude generates implementation
project/
  CLAUDE.md
  scripts/
    build_scene01.py
    build_scene02.py
    ...
  scenes/
    scene01.blend ... scene08.blend
  assets/
    archival/  (licensed and credited)
    models/    (verified CC0/permissive)
    sfx/
    music/
  audio/
    scene01.wav ... scene08.wav
  output/
    scene01_frames/ ...
    scene01.mp4 ...
    final_1617_1080p.mp4
    subtitles_mn.srt

### Rendering strategy
- Stage A: only Scene 01, 7–10 second preview, 960x540 / 24fps, Eevee.
- Stage B: Scene 01 final render (1920x1080), quick color and subtitle check.
- Stage C: Render 3–4 high-impact Blender scenes as hero shots (each ≤20 seconds); use archival/2.5D 2D planes for the rest to save time.
- Stage D: Split speech by scene and generate voice WAV. Don't ask TTS to guess historical quote voice acting.
- Stage E: Edit scenes and source-safe stills in Kdenlive. Add overlays in Kdenlive or Blender. Music below VO.
- Stage F: export final H.264 mp4 1080p 24fps + SRT. Rewatch and verify sync and factual claims.

### Typical Blender shell commands (once scripts exist; adjust to generated code)
```bash
blender --background --python scripts/build_scene01.py
blender --background scenes/scene01.blend --render-anim
```
### Typical FFmpeg image sequence to video
```bash
ffmpeg -framerate 24 -i output/scene01_frames/frame_%05d.png -c:v libx264 -pix_fmt yuv420p -crf 18 output/scene01.mp4
```

### Failure paths
- Slow render: halve internal samples, use Eevee, disable costly volumetrics and RTX-only features, render 540p previews.
- Model assets absent: use parametric silhouettes/primitive models rather than failing at external downloads.
- Archive photo usage rights unclear: replace with clearly artistic re-creation, cite research without embedding unlicensed image.
- ElevenLabs pronunciations incorrect: split into 1–2 sentence chunks, spell dates and unusual names phonetically, and manually crosscheck.
- Automatic music too loud: sidechain or manually duck to ensure narration is always dominant.
