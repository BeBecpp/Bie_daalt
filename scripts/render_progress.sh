#!/usr/bin/env bash
# Per-scene progress of the final 1080p render.
cd "$(dirname "$0")/.."
source config/final_cut.env
tot=0; done_=0
for S in 01 02 03 04 05 06 07 08 09; do
  DV=D$S; N=$(python3 -c "print(int(round(${!DV}*24)))")
  h=$(find output/final/frames/scene$S -name 'frame_*.png' -size +10k 2>/dev/null | wc -l)
  printf "scene %s: %4d / %4d\n" "$S" "$h" "$N"; tot=$((tot+N)); done_=$((done_+h))
done
echo "TOTAL: $done_ / $tot frames ($(( 100*done_/tot ))%)"
