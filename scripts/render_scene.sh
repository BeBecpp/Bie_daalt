#!/usr/bin/env bash
# Build + render + encode one scene.
#
#   scripts/render_scene.sh 01                 # 960x540 preview, Cycles CPU
#   scripts/render_scene.sh 01 final eevee     # 1920x1080, EEVEE (GPU laptop)
#   DURATION=17 scripts/render_scene.sh 01     # stretch to the narration length
#   STILLS=1,96,192 scripts/render_scene.sh 01 # only review stills
set -euo pipefail
cd "$(dirname "$0")/.."

SCENE=${1:?scene number, e.g. 01}
QUALITY=${2:-preview}
ENGINE=${3:-cycles}
BLENDER=${BLENDER:-blender}
EXTRA=()
[[ -n "${DURATION:-}" ]] && EXTRA+=(--duration "$DURATION")
[[ -n "${SAMPLES:-}" ]] && EXTRA+=(--samples "$SAMPLES")

if [[ -n "${STILLS:-}" ]]; then
  "$BLENDER" -b --factory-startup --python "scripts/build_scene${SCENE}.py" -- \
    --quality "$QUALITY" --engine "$ENGINE" --stills "$STILLS" "${EXTRA[@]}"
  exit 0
fi

"$BLENDER" -b --factory-startup --python "scripts/build_scene${SCENE}.py" -- \
  --quality "$QUALITY" --engine "$ENGINE" --render "${EXTRA[@]}"

D=${DURATION:-8}
HIT=$(python3 -c "print(5.5*$D/8)")
scripts/encode.sh "output/scene${SCENE}_${QUALITY}_frames" "output/scene${SCENE}_${QUALITY}.mp4" --temp-sfx "$HIT"
