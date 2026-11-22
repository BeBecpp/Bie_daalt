#!/usr/bin/env bash
# FINAL 1920x1080, true 24 fps (every frame rendered), Cycles CPU lean profile
# (--fast-final: 4 spp + OIDN high quality). One Blender process at a time.
# Frame-level resumable: existing PNGs are skipped (use_overwrite off), so the
# script can simply be started again after an interruption.
#
#   scripts/render_final.sh                  # all scenes in config/final_cut.env order
#   SCENES="07" scripts/render_final.sh
#   ENGINE=eevee scripts/render_final.sh     # on a machine with a real GPU
set -uo pipefail
cd "$(dirname "$0")/.."
source config/final_cut.env
BLENDER=${BLENDER:-blender}
ENGINE=${ENGINE:-cycles}
SCENES=${SCENES:-$ORDER}
mkdir -p output/final/frames output/logs
for S in $SCENES; do
  DV="D$S"; D=${!DV}
  N=$(python3 -c "print(int(round($D*24)))")
  OUT="output/final/frames/scene$S"
  SCRIPT="scripts/build_scene$S.py"; [[ "$S" == "09" ]] && SCRIPT="scripts/build_credits.py"
  EXTRA=(); [[ "$S" == "01" ]] && EXTRA+=(--hit "$H01")
  have=$(find "$OUT" -name 'frame_*.png' -size +10k 2>/dev/null | wc -l)
  if [[ $have -ge $N ]]; then echo "[1617] scene $S complete ($have/$N frames)"; continue; fi
  echo "[1617] === scene $S final 1080p: $D s, $N frames, $have done ($(date '+%d %H:%M')) ==="
  # remove 0-byte/placeholder frames left by an interrupted run so they get re-rendered
  find "$OUT" -name 'frame_*.png' -size -10k -delete 2>/dev/null
  START=$(date +%s)
  "$BLENDER" -b --factory-startup --python "$SCRIPT" -- --quality final --fast-final --engine "$ENGINE" \
      --render --no-save --duration "$D" --out "$OUT" "${EXTRA[@]}" >> "output/logs/final_scene$S.log" 2>&1
  have=$(find "$OUT" -name 'frame_*.png' -size +10k 2>/dev/null | wc -l)
  echo "[1617] scene $S: $have/$N frames ($(( ($(date +%s) - START) / 60 )) min)"
done
