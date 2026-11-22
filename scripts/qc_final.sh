#!/usr/bin/env bash
# Final QC for output/final/16_17_Republic_Day_FINAL_1080p.mp4 -> output/final/QC_REPORT.txt
set -uo pipefail
cd "$(dirname "$0")/.."
F=${1:-output/final/16_17_Republic_Day_FINAL_1080p.mp4}
R=output/final/QC_REPORT.txt
SRT=output/final/16_17_subtitles_mn.srt
{
echo "QC REPORT — $F"
echo "generated: $(date -u '+%Y-%m-%d %H:%M UTC')"
echo
echo "== streams"
ffprobe -v error -show_entries stream=index,codec_type,codec_name,profile,width,height,display_aspect_ratio,pix_fmt,r_frame_rate,avg_frame_rate,sample_rate,channels,bit_rate:stream_disposition=default -of compact "$F"
echo
echo "== container"
ffprobe -v error -show_entries format=duration,size,bit_rate -of compact "$F"
echo "size_MB: $(du -m "$F" | cut -f1)"
echo
echo "== decoded video frames (count_frames)"
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$F"
echo
echo "== black sections (>=0.4 s, luma<10%) — expected: opening fade-in, final fade-out"
ffmpeg -hide_banner -i "$F" -vf "blackdetect=d=0.4:pix_th=0.10" -an -f null - 2>&1 | grep -o "black_start.*" || echo "none"
echo
echo "== frozen sections (>=4 s, -60 dB)"
ffmpeg -hide_banner -i "$F" -vf "freezedetect=n=-60dB:d=4" -an -f null - 2>&1 | grep -oE "freeze_(start|duration|end).*" || echo "none"
echo
echo "== loudness (EBU R128)"
ffmpeg -hide_banner -i "$F" -vn -af ebur128=peak=true -f null - 2>&1 | grep -A12 "Summary:" | grep -E "I:|LRA:|Peak:"
echo
echo "== subtitles"
echo "cues: $(grep -c -- '-->' "$SRT")"
python3 - "$SRT" "$F" <<'EOF'
import re, subprocess, sys
srt, f = sys.argv[1], sys.argv[2]
dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
ts = re.findall(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", open(srt,encoding="utf-8").read())
bad = [i for i,t in enumerate(ts,1) if (int(t[4])*3600+int(t[5])*60+int(t[6])+int(t[7])/1000) > dur]
lines = [l for l in open(srt,encoding="utf-8").read().split("\n") if l and not l[0].isdigit()]
print("cues beyond end:", bad or "none", "| longest line chars:", max(len(l) for l in lines))
EOF
} | tee "$R"
# representative frames: mid-point of every segment + 16:17 moments
python3 - <<'EOF'
import json, subprocess
t = json.load(open("output/final/final_timeline.json"))
pts = [(s["segment"], (s["start"] + s["end"]) / 2) for s in t["segments"]]
for i, (name, ts) in enumerate(pts):
    subprocess.run(["ffmpeg","-loglevel","error","-y","-ss",f"{ts:.2f}","-i",t["file"],"-frames:v","1",
                    "-vf","scale=640:-1",f"output/final/qc_{i:02d}_{name}.png"])
subprocess.run("ffmpeg -loglevel error -y -pattern_type glob -i 'output/final/qc_*.png' "
               "-vf tile=4x3:padding=4 -frames:v 1 output/final/QC_contact_sheet.png", shell=True)
print("contact sheet: output/final/QC_contact_sheet.png")
EOF
