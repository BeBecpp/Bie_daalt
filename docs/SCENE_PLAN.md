# Implementation plan — remaining scenes

Order (from `07_start_with_claude.txt`): **06 → 02 → 08 → 03 → 04 → 05 → 07**.
Each scene gets `scripts/build_sceneNN.py` built on `scripts/lib/` and takes the
same CLI (`--quality`, `--engine`, `--duration`, `--stills`, `--render`). Its beats
are defined relative to `--duration`, so every shot can be stretched to its real VO WAV.

| # | Slug | Core 3D idea (reuses) | Motion | Historical guardrails |
|---|---|---|---|---|
| 06 | constitution_1924 | Desk set + manuscript (lib.props), 18 sheets fanned in a page-turn montage (shape-key or bend modifier); hall implied by column/bench **silhouettes** with volumetric window light; the watch returns at 16:17 | dolly from table → slow rise into "gallery" of silhouettes, match-cut on the clock | 77 delegates; 6 chapters / 50 articles; 16:17 on 26 Nov; **no opening date of the Khural**; manuscript stays abstract or a cleared scan; no fake delegate faces |
| 02 | foundation_1206 | Displaced-plane steppe + wind-animated grass (GN), dawn sun, low-poly horse/rider silhouettes on a path, felt-tent (ger) silhouettes | low-angle wide → orbit, parallax dust | Great Mongol State, 1206; Khuraldai ≠ modern parliament; **no invented Yassa text**, no confident face of Chinggis Khan |
| 08 | legacy | Sunrise over steppe (from 02) → timeline of floating date plates 1206/1911/1921/1924 → 1940/1960/1992 → return to manuscript + title | long pullback, final 4–5 s silence + source card | constitutions of 1940, 1960, 1992; dates are facts, symbols are metaphors |
| 03 | independence_1911 | 2.5D layered card stack (planes with alpha), animated cartographic line drawn with GN curve-trim; Bogd Khan photo **only if cleared**, otherwise a labelled silhouette | parallax track through layers | 29 Dec 1911; no modern borders projected onto the 1911 state |
| 04 | revolution_1921 | Cool, desaturated layered "archive" planes (placeholders), date cards, routes without unsourced borders | slow track + gentle handheld (noise modifier, low amplitude) | monarchy **not** abolished in 1921; Bogd Khan remained head of state |
| 05 | decision_1924 | Oblique desk macro (reuses Scene 01 set), commission papers, turned pages | desk macro, light changes from day to evening | Bogd Khan died May 1924; drafting considered several models; Soviet advisors' role not erased |
| 07 | rights_and_limits | Motion-graphics 3D plates: monarchy → republic; eligibility icons with **criteria**; excluded groups (Art. 35) | infographic 3D transitions | Art. 34 eligibility under occupational criteria; Art. 35 exclusions; **not** universal suffrage; not equal to modern democracy |

## Shared work still to do
- `scripts/render_all.sh`: loops over scenes and stitches with an FFmpeg concat list, with crossfades only where the storyboard asks for them.
- `scripts/make_srt.py`: SRT from `docs/director_pack/08_voiceover_paste_ready/*.txt` and the measured WAV durations (1–2 lines, ≤ 42 chars/line).
- Closing source card (4–6 s) using the credits template from `06_asset_credits.md`.
