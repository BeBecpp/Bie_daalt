#!/usr/bin/env bash
# Encode a rendered PNG sequence into an H.264 MP4 (+ optional audio) and a
# contact sheet for review.
#
#   scripts/encode.sh output/scene01_preview_frames output/scene01_preview.mp4 [audio.wav|--temp-sfx HIT_SECONDS]
#
# --temp-sfx writes a self-synthesised scratch track (clock ticks + a low
# pulse on the 16:17 beat) so timing can be judged before the real VO/SFX
# exist. It is NOT final audio; replace it in Kdenlive or with a WAV.
set -euo pipefail

FRAMES_DIR=${1:?frames dir}
OUT=${2:?output mp4}
AUDIO=${3:-}
HIT=${4:-5.5}
FPS=24

N=$(ls "$FRAMES_DIR"/frame_*.png | wc -l)
DUR=$(python3 -c "print($N/$FPS)")
mkdir -p "$(dirname "$OUT")"

if [[ "$AUDIO" == "--temp-sfx" ]]; then
  SFX="${OUT%.mp4}_temp_sfx.wav"
  # ticks every whole clock second (clock reaches 16:17:00 at t=HIT),
  # brighter 'tock' + 55 Hz pulse on the hit, fades in with the picture.
  ffmpeg -loglevel error -y -f lavfi -i "aevalsrc='\
0.30*sin(2*PI*2600*t)*exp(-70*mod(t-$HIT+100,1))*(1-exp(-t*2))\
+0.20*sin(2*PI*1300*t)*exp(-90*mod(t-$HIT+100,1))*(1-exp(-t*2))\
+0.45*sin(2*PI*55*t)*exp(-2.2*(t-$HIT))*gte(t,$HIT)\
+0.25*sin(2*PI*1760*t)*exp(-6*(t-$HIT))*gte(t,$HIT)\
:s=48000:d=$DUR'" -af "afade=t=in:d=0.8" "$SFX"
  AUDIO="$SFX"
fi

if [[ -n "$AUDIO" ]]; then
  ffmpeg -loglevel error -y -framerate $FPS -i "$FRAMES_DIR/frame_%04d.png" -i "$AUDIO" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -c:a aac -b:a 192k -shortest \
    -movflags +faststart "$OUT"
else
  ffmpeg -loglevel error -y -framerate $FPS -i "$FRAMES_DIR/frame_%04d.png" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart "$OUT"
fi
echo "[1617] wrote $OUT ($N frames, ${DUR}s)"

# contact sheet: one frame per second, 4 columns
SHEET="${OUT%.mp4}_contact.png"
ffmpeg -loglevel error -y -framerate $FPS -i "$FRAMES_DIR/frame_%04d.png" \
  -vf "select='not(mod(n\,24))',scale=480:-1,tile=4x2:padding=6:color=black" -frames:v 1 "$SHEET"
echo "[1617] wrote $SHEET"
