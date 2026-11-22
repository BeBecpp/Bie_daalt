#!/usr/bin/env bash
# 540p rough cut: every scene with the --rough profile (4 samples, fast denoise,
# every 2nd frame = 12 fps doubled to 24 fps at encode). One scene at a time
# (no parallel CPU contention). Resumable: a scene whose MP4 exists is skipped.
#
#   scripts/render_rough.sh            # all scenes in config/rough_cut.env order
#   SCENES="02 03" scripts/render_rough.sh
#   FORCE=1 SCENES="03" scripts/render_rough.sh   # re-render (e.g. after photos arrive)
set -uo pipefail
cd "$(dirname "$0")/.."
source config/rough_cut.env
BLENDER=${BLENDER:-blender}
SCENES=${SCENES:-$ORDER}
mkdir -p output/rough output/logs
for S in $SCENES; do
  MP4="output/rough/scene${S}_rough.mp4"
  DVAR="D${S}"
  if [[ -f "$MP4" && -z "${FORCE:-}" ]]; then echo "[1617] scene $S rough exists, skipping"; continue; fi
  OUT="output/rough/scene${S}_frames"
  [[ -n "${FORCE:-}" ]] && find "$OUT" -name 'frame_*.png' -delete 2>/dev/null
  echo "[1617] === scene $S rough, ${!DVAR}s ($(date +%H:%M:%S)) ==="
  START=$(date +%s)
  "$BLENDER" -b --factory-startup --python "scripts/build_scene${S}.py" -- \
      --quality preview --engine cycles --rough --render --no-save --duration "${!DVAR}" --out "$OUT" \
      > "output/logs/rough_scene${S}.log" 2>&1
  RC=$?
  N=$(find "$OUT" -name 'frame_*.png' 2>/dev/null | wc -l)
  if [[ $RC -ne 0 || $N -eq 0 ]]; then echo "[1617] scene $S FAILED rc=$RC frames=$N (output/logs/rough_scene${S}.log)"; continue; fi
  # 12 fps renders -> 24 fps (each frame shown twice); exact length = D seconds
  ffmpeg -loglevel error -y -framerate 12 -pattern_type glob -i "$OUT/frame_*.png" \
      -vf "fps=24,format=yuv420p" -t "${!DVAR}" -c:v libx264 -crf 20 -preset medium "$MP4"
  echo "[1617] scene $S -> $MP4 ($N frames, $(( $(date +%s) - START ))s)"
done
