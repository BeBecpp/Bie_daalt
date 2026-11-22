#!/usr/bin/env bash
# Render every scene and assemble the film.
#
#   scripts/render_all.sh                    # 540p preview, Cycles CPU
#   scripts/render_all.sh final eevee        # 1080p on a GPU laptop
#   SAMPLES=10 SCENES="02 06" scripts/render_all.sh
#
# Durations come from config/scene_durations.env if present (seconds per
# scene, e.g. D06=52 once the narration WAV is measured), else the defaults
# in each builder (storyboard timings).
set -uo pipefail
cd "$(dirname "$0")/.."
QUALITY=${1:-preview}
ENGINE=${2:-cycles}
BLENDER=${BLENDER:-blender}
SCENES=${SCENES:-"01 02 03 04 05 06 07 08"}
[[ -f config/scene_durations.env ]] && source config/scene_durations.env
mkdir -p output/logs

for S in $SCENES; do
  OUTDIR="output/scene${S}_${QUALITY}_frames"
  EXTRA=()
  DVAR="D${S}"; [[ -n "${!DVAR:-}" ]] && EXTRA+=(--duration "${!DVAR}")
  [[ -n "${SAMPLES:-}" ]] && EXTRA+=(--samples "$SAMPLES")
  # resume: skip scenes whose MP4 already exists
  if [[ -f "output/scene${S}_${QUALITY}.mp4" ]]; then echo "[1617] scene $S done, skipping"; continue; fi
  echo "[1617] === scene $S ($(date +%H:%M)) ==="
  "$BLENDER" -b --factory-startup --python "scripts/build_scene${S}.py" -- \
     --quality "$QUALITY" --engine "$ENGINE" --render "${EXTRA[@]}" > "output/logs/scene${S}.log" 2>&1 \
     || { echo "[1617] scene $S FAILED (see output/logs/scene${S}.log)"; continue; }
  ffmpeg -loglevel error -y -framerate 24 -i "$OUTDIR/frame_%04d.png" -c:v libx264 -pix_fmt yuv420p \
     -crf 18 -movflags +faststart "output/scene${S}_${QUALITY}.mp4"
  echo "[1617] scene $S -> output/scene${S}_${QUALITY}.mp4"
done

# assemble (picture only; narration/music are mixed by scripts/mix_audio.sh or in Kdenlive)
LIST=output/concat_${QUALITY}.txt
: > "$LIST"
for S in 01 02 03 04 05 06 07 08; do
  [[ -f "output/scene${S}_${QUALITY}.mp4" ]] && echo "file 'scene${S}_${QUALITY}.mp4'" >> "$LIST"
done
ffmpeg -loglevel error -y -f concat -safe 0 -i "$LIST" -c copy "output/film_${QUALITY}_picture.mp4" \
  && echo "[1617] assembled output/film_${QUALITY}_picture.mp4"
