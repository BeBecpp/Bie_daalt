#!/usr/bin/env python3
"""Assemble the FINAL film from the native 1080p frame sequences.

    python3 scripts/assemble_final.py            # needs every scene complete
    python3 scripts/assemble_final.py --check    # only report frame completeness

Output  output/final/16_17_Republic_Day_FINAL_1080p.mp4
        1920x1080, 24 fps (unique frames, no duplication), H.264 High yuv420p CRF 18,
        AAC stereo 48 kHz 256 kb/s, soft Mongolian subtitles (default track).
Also    output/final/16_17_subtitles_mn.srt, output/final/final_timeline.json

Timeline: 4 s opening card + scenes 01-08 + end credits (09), 0.75 s crossfades.
Audio (all original / licensed):
  * ElevenLabs Eleven v4 «Bilguun» narration, audio/narration/sceneNN.mp3, placed
    at scene start + lead (config/final_cut.env); subtitles from the measured
    alignment (output/narration_alignment.json, scripts/narration.py)
  * original score (audio/music/score_ambient.wav, scripts/make_score.py),
    side-chain ducked under the voice, lifted for the credits
  * synthesised SFX: clock ticks (scene 01; 16:17 in scene 06), soft transition
    swells, steppe wind (02, 08), room tone (desk scenes)
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIN = os.path.join(ROOT, "output", "final")
FRAMES = os.path.join(FIN, "frames")
FONT_SERIF = os.path.join(ROOT, "assets", "fonts", "NotoSerif-SemiBold.ttf")
FONT_SANS = os.path.join(ROOT, "assets", "fonts", "NotoSans-Regular.ttf")
W, H, FPS = 1920, 1080, 24
ORDER = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
OUTNAME = "16_17_Republic_Day_FINAL_1080p.mp4"


def cfg():
    c = {}
    for line in open(os.path.join(ROOT, "config", "final_cut.env"), encoding="utf-8"):
        for m in re.finditer(r"([A-Z]+\d*)=([\d.]+)", line.split("#")[0]):
            c[m.group(1)] = float(m.group(2))
    return c


def run(cmd):
    print("+", " ".join(str(x) for x in cmd[:8]), "...", flush=True)
    subprocess.run(cmd, check=True)


def frame_status(c):
    st = {}
    for s in ORDER:
        n = int(round(c[f"D{s}"] * FPS))
        d = os.path.join(FRAMES, f"scene{s}")
        have = sorted(f for f in os.listdir(d) if f.startswith("frame_") and
                      os.path.getsize(os.path.join(d, f)) > 10240) if os.path.isdir(d) else []
        st[s] = (len(have), n)
    return st


def encode_scene(s, n):
    out = os.path.join(FIN, "clips", f"scene{s}.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    src = os.path.join(FRAMES, f"scene{s}", "frame_%04d.png")
    if os.path.exists(out) and os.path.getmtime(out) > max(
            os.path.getmtime(os.path.join(FRAMES, f"scene{s}", f)) for f in os.listdir(os.path.join(FRAMES, f"scene{s}"))):
        return out
    run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-start_number", "1", "-i", src,
         "-frames:v", str(n), "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", out])
    return out


def opening_card(path, dur):
    d = os.path.join(FIN, "clips")
    t1, t2 = os.path.join(d, "_t1.txt"), os.path.join(d, "_t2.txt")
    open(t1, "w", encoding="utf-8").write("16:17 — Монгол төрийн түүхэн эргэлт")
    open(t2, "w", encoding="utf-8").write("10-р ангийн Монголын түүхийн бие даалт · баримтат кино")
    vf = (f"drawtext=fontfile={FONT_SERIF}:textfile={t1}:fontcolor=0xF1E4CC:fontsize=78:x=(w-tw)/2:y=h/2-96,"
          f"drawtext=fontfile={FONT_SANS}:textfile={t2}:fontcolor=0xC8A56C:fontsize=38:x=(w-tw)/2:y=h/2+28,"
          f"fade=t=in:st=0:d=1.0,fade=t=out:st={dur - 1.0}:d=1.0,format=yuv420p")
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0a0c12:s={W}x{H}:r={FPS}:d={dur}",
         "-vf", vf, "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", path])


def srt_time(t):
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"


def probe_dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout)


def main():
    c = cfg()
    st = frame_status(c)
    for s, (h, n) in st.items():
        print(f"scene {s}: {h}/{n} frames {'OK' if h >= n else 'INCOMPLETE'}")
    if "--check" in sys.argv:
        return
    dry = "--dry" in sys.argv          # validate the whole graph with stand-in clips (not a deliverable)
    missing = [s for s, (h, n) in st.items() if h < n]
    if missing and not dry:
        sys.exit(f"cannot assemble: incomplete scenes {missing}")
    align = json.load(open(os.path.join(ROOT, "output", "narration_alignment.json"), encoding="utf-8"))
    if align["missing"]:
        sys.exit(f"narration missing for scenes {align['missing']}")
    OPEN, X = c["OPENING"], c["XFADE"]
    clips = [os.path.join(FIN, "clips", "_opening.mp4")]
    opening_card(clips[0], OPEN)
    if dry:
        for s in ORDER:
            p = os.path.join(FIN, "clips", f"_dry{s}.mp4")
            run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                 f"testsrc2=s={W}x{H}:r={FPS}:d={c['D' + s]}", "-c:v", "libx264", "-preset", "ultrafast",
                 "-pix_fmt", "yuv420p", p])
            clips.append(p)
    else:
        clips += [encode_scene(s, st[s][1]) for s in ORDER]
    lens = [probe_dur(p) for p in clips]
    names = [None] + ORDER

    timeline, t = [], 0.0
    for i, (p, L) in enumerate(zip(clips, lens)):
        start = 0.0 if i == 0 else t - X
        timeline.append({"segment": names[i] or "opening", "start": round(start, 3), "end": round(start + L, 3),
                         "length": round(L, 3)})
        t = start + L
    total = t

    # ---------- subtitles from the measured narration alignment
    cues = []
    for seg in timeline[1:]:
        s = seg["segment"]
        a = align["scenes"].get(s)
        if not a:
            continue
        off = seg["start"] + c[f"L{s}"]
        seg["narration"] = {"file": a["file"], "start": round(off, 3), "end": round(off + a["audio"]["duration"], 3),
                            "duration": a["audio"]["duration"], "alignment": a["method"]}
        if off + a["audio"]["duration"] > seg["end"] - 0.3:
            print(f"WARNING scene {s}: narration overruns the scene")
        for cu in a["cues"]:
            cues.append((off + cu["start"], off + cu["end"] - 0.05, cu["text"]))
    srt = os.path.join(FIN, "16_17_subtitles_mn.srt")
    with open(srt, "w", encoding="utf-8") as fh:
        for i, (a, b, txt) in enumerate(cues, 1):
            fh.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")

    # ---------- video: chained crossfades + gentle fade-out at the very end
    inputs = []
    for p in clips:
        inputs += ["-i", p]
    vf, prev, acc = [], "[0:v]", lens[0]
    for i in range(1, len(clips)):
        off = acc - X
        vf.append(f"{prev}[{i}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[v{i}]")
        prev, acc = f"[v{i}]", off + lens[i]
    vf.append(f"{prev}fade=t=out:st={total - 1.5:.3f}:d=1.5,format=yuv420p[vout]")

    # ---------- audio
    k = len(clips)
    seg = {x["segment"]: x for x in timeline}
    s01, s06 = seg["01"], seg["06"]
    hit1 = s01["start"] + c["H01"]
    hit6 = s06["start"] + 15.6 * c["D06"] / 34.0
    w6a, w6b = s06["start"] + 11.6 * c["D06"] / 34.0, s06["start"] + 16.2 * c["D06"] / 34.0
    tick = ("(sin(2*PI*2600*t)*exp(-70*mod(t-{h}+1000,1))*0.26+sin(2*PI*1300*t)*exp(-90*mod(t-{h}+1000,1))*0.16)")
    swells = "+".join(f"0.5*exp(-pow((t-{x['start'] + X / 2:.3f})/0.55,2))" for x in timeline[1:])
    sfx = (f"{tick.format(h=hit1)}*between(t,{s01['start'] + 0.6:.2f},{s01['end'] - 0.4:.2f})"
           f"+0.40*sin(2*PI*55*t)*exp(-2.0*(t-{hit1:.3f}))*gte(t,{hit1:.3f})*lte(t,{hit1 + 3:.3f})"
           f"+{tick.format(h=hit6)}*between(t,{w6a:.2f},{w6b:.2f})"
           f"+0.32*sin(2*PI*55*t)*exp(-2.0*(t-{hit6:.3f}))*gte(t,{hit6:.3f})*lte(t,{hit6 + 3:.3f})")
    a_in = ["-f", "lavfi", "-i", f"aevalsrc='{sfx}':s=48000:c=stereo:d={total:.3f}",          # k   ticks
            "-i", os.path.join(ROOT, "audio", "music", "score_ambient.wav"),                    # k+1 score
            "-f", "lavfi", "-i", f"anoisesrc=c=pink:r=48000:a=0.5:d={total:.3f}",                # k+2 swell noise
            "-f", "lavfi", "-i", f"anoisesrc=c=brown:r=48000:a=0.6:d={total:.3f}"]               # k+3 wind/room
    vo = [x for x in timeline[1:] if x.get("narration")]
    for x in vo:
        a_in += ["-i", os.path.join(ROOT, x["narration"]["file"])]
    wind = "+".join(f"between(t,{seg[s]['start']:.2f},{seg[s]['end']:.2f})" for s in ("02", "08"))
    room = "+".join(f"between(t,{seg[s]['start']:.2f},{seg[s]['end']:.2f})" for s in ("01", "05"))
    cred = seg["09"]
    af = [
        f"[{k}:a]volume=0.55[ticks]",
        f"[{k+1}:a]atrim=0:{total:.3f},volume='0.20+0.30*between(t,{cred['start']:.2f},{total:.2f})':eval=frame,"
        f"afade=t=in:st=0:d=3,afade=t=out:st={total - 4:.2f}:d=4[mus]",
        f"[{k+2}:a]aformat=channel_layouts=mono,highpass=f=400,lowpass=f=3500,"
        f"volume='0.10*({swells})':eval=frame,pan=stereo|c0=c0|c1=c0[swell]",
        f"[{k+3}:a]aformat=channel_layouts=mono,lowpass=f=500,"
        f"volume='(0.05+0.03*sin(2*PI*t/7))*({wind})+0.012*({room})':eval=frame,pan=stereo|c0=c0|c1=c0[amb]",
    ]
    labels = []
    for i, x in enumerate(vo):
        ms = int(round(x["narration"]["start"] * 1000))
        af.append(f"[{k+4+i}:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.15,adelay={ms}|{ms},"
                  f"apad=whole_dur={total:.3f}[vo{i}]")
        labels.append(f"[vo{i}]")
    af.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,asplit=2[vox][key]")
    af.append("[mus][swell][amb]amix=inputs=3:normalize=0[bed]")
    af.append("[bed][key]sidechaincompress=threshold=0.015:ratio=10:attack=30:release=700:makeup=1[bedd]")
    af.append("[vox][bedd][ticks]amix=inputs=3:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,"
              "alimiter=limit=0.89:level=false,aresample=48000[aout]")
    srt_idx = k + 4 + len(vo)
    out = os.path.join(FIN, "_DRY_RUN_not_final.mp4" if dry else OUTNAME)
    cmd = (["ffmpeg", "-loglevel", "error", "-y"] + inputs + a_in + ["-i", srt,
           "-filter_complex", ";".join(vf + af), "-map", "[vout]", "-map", "[aout]", "-map", f"{srt_idx}:s",
           "-c:v", "libx264", "-profile:v", "high", "-crf", "18", "-preset", "ultrafast" if dry else "slow",
           "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
           "-c:s", "mov_text", "-metadata:s:s:0", "language=mon", "-disposition:s:0", "default",
           "-metadata", "title=16:17 — Монгол төрийн түүхэн эргэлт", "-metadata", "comment=10Б анги",
           "-movflags", "+faststart", "-t", f"{total:.3f}", out])
    run(cmd)
    json.dump({"file": os.path.relpath(out, ROOT), "total_seconds": round(total, 3), "segments": timeline,
               "subtitle_cues": len(cues)}, open(os.path.join(FIN, "final_timeline.json"), "w"),
              ensure_ascii=False, indent=2)
    print(f"[1617] {out}  {total:.2f}s  {len(cues)} cues")


if __name__ == "__main__":
    main()
