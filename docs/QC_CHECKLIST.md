# QC checklist & review log

## Per-scene self-check (run before any full render)
- [ ] Rendered `--stills` at start / middle / key beat / end and looked at every one
- [ ] Camera actually moves (position **and** framing change); no random jitter
- [ ] Light is dynamic (intensity/position animated) and shadows read clearly
- [ ] Clear depth separation: foreground / subject / background (DOF or parallax layers)
- [ ] Title-safe: all text inside the central 90%; subtitles ≥ 4.5:1 contrast against the frame
- [ ] Cyrillic renders with no missing glyphs (check Өө Үү specifically)
- [ ] Reconstruction label present on every 3D-reconstruction shot
- [ ] No Cyrillic painted on any "original" 1924 document
- [ ] No invented quotes; no complete Их засаг text; 1206 ≠ 1924 state
- [ ] No modern flag in 1911–1924 shots; no universal suffrage claim for 1924
- [ ] No specific opening date for the First Great Khural
- [ ] Every asset in the frame is listed in `ASSET_MANIFEST.md` with a verified license
- [ ] Shot length is driven by `--duration` (fits the VO WAV)

## Final delivery checklist
- [ ] `output/final_1617_1080p.mp4`: 1920×1080, 24 fps, H.264 yuv420p, AAC
- [ ] `output/subtitles_mn.srt`: Mongolian, checked against `02_narration_mn.md`
- [ ] Narration intelligible over music at every point; last ~4 s without narration
- [ ] Closing source card 4–6 s (sources from `03_fact_check_sources.md`)
- [ ] `ffprobe` check of resolution/fps/codec; full re-watch for sync and facts

---

## Scene 01 POC — review log (Blender 4.5.16, Cycles CPU, 960×540)

| Round | Frames checked | Problem seen in the renders | Fix |
|---|---|---|---|
| Texture v1 | albedo PNG | Pseudo-script looked like hooks/music notes; stains read as coffee-cup rings; fibres too visible | Rewrote the glyph generator (brush wedges, loops, word tails, 22 tighter columns); blotchy noise-warped stains; subtler fibres |
| 1 | 20, 66, 103, 132, 192 | **Watch dial rendered black** | — (see round 2/3) |
| 1 | 66 | Manuscript macro almost entirely out of focus (f/3.2 at ~12 cm) | f/5.6–6.3 for the macro, focus empty follows the aim point |
| 1 | all | Light too salmon/pink; wood grain looked corrugated; dust sparse; push-in after 16:17 too small; reconstruction label tiny | 3700 K key; finer, lower-contrast wood with less bump; 2× dust and larger motes; longer end move; label 0.22 → 0.27 |
| 2 | 66, 103, 150 | Dial still black even with a transparent/glossy crystal | Debug render with the crystal hidden showed the dial correctly, so the crystal was the culprit: its solidified shell caused total internal reflection on the inner face. Single-surface crystal, fresnel only on front faces |
| 3 | 120, 192 | Dial correct (4:17, red inner "16"), but end frame too tight: watch cropped and title overlapping it | Pulled the end camera back and up; aim point below the dial puts the watch in the upper ⅔ |
| 4–5 | 1, 30, 133, 192 | Framing OK; title fully on the desk; whole watch visible | Approved for full render |

POC acceptance (from `01_storyboard.md`), all met in the rendered frames:
real 3D parchment ✔ · animated 16:17 watch ✔ · moving camera ✔ · lights/shadows ✔ ·
readable Mongolian heading ✔ · exportable frames ✔

Known limitations of the POC:
- Preview uses 16 samples + denoise, so very fine dust can shimmer slightly. Final quality uses 128 samples.
- The 8 s POC is shorter than the storyboard's 17 s slot. Use `--duration 17` once the VO WAV exists.
- The scratch audio is synthesised ticks only. There is no narration or music yet.
