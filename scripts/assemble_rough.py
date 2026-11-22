#!/usr/bin/env python3
"""Assemble the 540p rough cut from output/rough/sceneNN_rough.mp4.

    python3 scripts/assemble_rough.py

Produces
  output/complete_rough_cut_540p.mp4   960x540, 24 fps, H.264 + AAC (+ soft mov_text subtitles)
  output/rough_cut_narration_mn.srt    narration TEXT timed to the cut (no voice-over exists yet)
  output/rough_cut_timeline.json       exact in/out of every segment

* 4 s opening card (Noto fonts, Cyrillic) then the 8 scenes with 0.75 s crossfades.
* Audio = verified ElevenLabs narration files (audio/narration/sceneNN.mp3, aligned by
  scripts/narration.py) placed LEAD seconds into each scene, + the original score
  (audio/music/score_ambient.wav) ducked under the voice, + scratch clock ticks.
  Scenes without a verified narration file get NO voice; their subtitle cues use
  provisional text-proportional timing and are flagged in rough_cut_timeline.json.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "output")
ROUGH = os.path.join(OUT, "rough")
FONT_SERIF = os.path.join(ROOT, "assets", "fonts", "NotoSerif-SemiBold.ttf")
FONT_SANS = os.path.join(ROOT, "assets", "fonts", "NotoSans-Regular.ttf")
VO_DIR = os.path.join(ROOT, "docs", "director_pack", "08_voiceover_paste_ready")
OPENING = 4.0
LEAD = {"01": 2.0}          # seconds from scene start to first word (default 1.2)
ALIGN = os.path.join(OUT, "narration_alignment.json")
XFADE = 0.75
W, H, FPS = 960, 540, 24


def env_durations():
    d = {}
    for line in open(os.path.join(ROOT, "config", "rough_cut.env"), encoding="utf-8"):
        m = re.match(r"D(\d\d)=([\d.]+)", line.strip())
        if m:
            d[m.group(1)] = float(m.group(2))
    return d


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def run(cmd):
    print("+", " ".join(cmd[:6]), "...")
    subprocess.run(cmd, check=True)


def opening_card(path, n_vo=0):
    txt = os.path.join(OUT, "rough", "_opening_title.txt")
    sub = os.path.join(OUT, "rough", "_opening_sub.txt")
    note = os.path.join(OUT, "rough", "_opening_note.txt")
    open(txt, "w", encoding="utf-8").write("16:17 — Монгол төрийн түүхэн эргэлт")
    open(sub, "w", encoding="utf-8").write("10-р ангийн Монголын түүхийн бие даалт · баримтат кино")
    msg = ("Ноорог эвлүүлэг · 540p, 12 fps урьдчилсан рендер" if n_vo == 8 else
           f"Ноорог эвлүүлэг · 540p, 12 fps урьдчилсан рендер · хүүрнэл {n_vo}/8 хэсэгт бэлэн")
    open(note, "w", encoding="utf-8").write(msg)
    vf = (f"drawtext=fontfile={FONT_SERIF}:textfile={txt}:fontcolor=0xF1E4CC:fontsize=40:x=(w-tw)/2:y=h/2-50,"
          f"drawtext=fontfile={FONT_SANS}:textfile={sub}:fontcolor=0xC8A56C:fontsize=20:x=(w-tw)/2:y=h/2+12,"
          f"drawtext=fontfile={FONT_SANS}:textfile={note}:fontcolor=0x9a8f7d:fontsize=14:x=(w-tw)/2:y=h-48,"
          f"fade=t=in:st=0:d=0.8,fade=t=out:st={OPENING - 0.8}:d=0.8,format=yuv420p")
    run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0b0a09:s={W}x{H}:r={FPS}:d={OPENING}",
         "-vf", vf, "-c:v", "libx264", "-crf", "18", path])


def sentences(text):
    parts = re.split(r"(?<=[.?!])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def wrap(s, n=42):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


def srt_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def build_srt(timeline, path, align):
    cues = []
    for seg in timeline:
        if not seg["scene"]:
            continue
        a = align.get(seg["scene"])
        if a:
            off = seg["start"] + LEAD.get(seg["scene"], 1.2)
            seg["narration"] = {"file": a["file"], "start": round(off, 3),
                                "end": round(off + a["audio"]["duration"], 3), "timing": a["method"]}
            for c in a["cues"]:
                cues.append((off + c["start"], off + c["end"] - 0.05, c["text"]))
            continue
        seg["narration"] = {"file": None, "timing": "PROVISIONAL text-proportional (no audio yet)"}
        vo = os.path.join(VO_DIR, f"scene_{seg['scene']}.txt")
        text = open(vo, encoding="utf-8").read()
        sents = []
        for s in sentences(text):
            lines = wrap(s)
            for i in range(0, len(lines), 2):          # max 2 lines per cue
                sents.append("\n".join(lines[i:i + 2]))
        t0 = seg["start"] + 0.6
        t1 = seg["end"] - (5.5 if seg["scene"] == "08" else 0.6)   # last ~5 s of the film: no narration
        total = sum(len(s) for s in sents)
        t = t0
        for s in sents:
            dur = (t1 - t0) * len(s) / total
            cues.append((t, t + dur - 0.08, s))
            t += dur
    with open(path, "w", encoding="utf-8") as fh:
        for i, (a, b, s) in enumerate(cues, 1):
            fh.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    return len(cues)


def main():
    durs = env_durations()
    align = json.load(open(ALIGN, encoding="utf-8"))["scenes"] if os.path.exists(ALIGN) else {}
    clips = [os.path.join(ROUGH, "_opening.mp4")]
    opening_card(clips[0], len(align))
    missing = [s for s in sorted(durs) if not os.path.exists(os.path.join(ROUGH, f"scene{s}_rough.mp4"))]
    if missing:
        sys.exit(f"missing rough scene clips: {missing}")
    clips += [os.path.join(ROUGH, f"scene{s}_rough.mp4") for s in sorted(durs)]
    lens = [probe_duration(c) for c in clips]

    # timeline with crossfades: each clip after the first starts XFADE earlier
    timeline, t = [], 0.0
    names = [None] + sorted(durs)
    for i, (c, L) in enumerate(zip(clips, lens)):
        start = t if i == 0 else t - XFADE
        timeline.append({"scene": names[i], "file": os.path.relpath(c, ROOT), "start": round(start, 3),
                         "end": round(start + L, 3), "length": round(L, 3)})
        t = start + L
    total = t

    # video: chained xfade
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    fc, prev, acc = [], "[0:v]", lens[0]
    for i in range(1, len(clips)):
        off = acc - XFADE
        out = f"[v{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XFADE}:offset={off:.3f}{out}")
        prev, acc = out, off + lens[i]
    fc.append(f"{prev}format=yuv420p[vout]")

    # scratch audio: clock ticks in scene 01 and in scene 06's watch shot (16:17 at 19.0/46 of the scene)
    s01 = timeline[1]
    s06 = next(x for x in timeline if x["scene"] == "06")
    hit1 = s01["start"] + 5.5 * durs["01"] / 8.0
    hit6 = s06["start"] + 19.0 * durs["06"] / 46.0
    w6a, w6b = s06["start"] + 13.8 * durs["06"] / 46.0, s06["start"] + 21.2 * durs["06"] / 46.0
    tick = "sin(2*PI*2600*t)*exp(-70*mod(t-{h}+1000,1))*0.28+sin(2*PI*1300*t)*exp(-90*mod(t-{h}+1000,1))*0.18"
    expr = (f"({tick.format(h=hit1)})*between(t,{s01['start']+0.8:.2f},{s01['end']:.2f})"
            f"+0.45*sin(2*PI*55*t)*exp(-2.2*(t-{hit1:.3f}))*gte(t,{hit1:.3f})*lte(t,{hit1+3:.3f})"
            f"+({tick.format(h=hit6)})*between(t,{w6a:.2f},{w6b:.2f})"
            f"+0.35*sin(2*PI*55*t)*exp(-2.2*(t-{hit6:.3f}))*gte(t,{hit6:.3f})*lte(t,{hit6+3:.3f})")
    srt = os.path.join(OUT, "rough_cut_narration_mn.srt")
    n_cues = build_srt(timeline, srt, align)
    final = os.path.join(OUT, "complete_rough_cut_540p.mp4")
    k = len(clips)
    a_inputs = ["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:c=stereo:d={total:.3f}"]   # k: ticks
    music = os.path.join(ROOT, "audio", "music", "score_ambient.wav")
    a_inputs += ["-i", music]                                                              # k+1: score
    vo = [seg for seg in timeline if seg.get("narration", {}).get("file")]
    for seg in vo:
        a_inputs += ["-i", os.path.join(ROOT, seg["narration"]["file"])]
    ai = k + 2
    afc = [f"[{k}:a]volume=0.6[ticks]",
           f"[{k+1}:a]atrim=0:{total:.3f},volume=0.22,afade=t=out:st={total-5:.2f}:d=5[mus]"]
    labels = []
    for i, seg in enumerate(vo):
        ms = int(seg["narration"]["start"] * 1000)
        afc.append(f"[{ai+i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},"
                   f"apad=whole_dur={total:.3f}[vo{i}]")
        labels.append(f"[vo{i}]")
    if labels:
        afc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,asplit=2[vox][key]")
        afc.append("[mus][key]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=600[musd]")
        afc.append("[vox][musd][ticks]amix=inputs=3:normalize=0,alimiter=limit=0.9[aout]")
    else:
        afc.append("[mus][ticks]amix=inputs=2:normalize=0,alimiter=limit=0.9[aout]")
    srt_idx = ai + len(vo)
    cmd = (["ffmpeg", "-loglevel", "error", "-y"] + inputs + a_inputs + ["-i", srt,
            "-filter_complex", ";".join(fc + afc), "-map", "[vout]", "-map", "[aout]", "-map", f"{srt_idx}:s",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "160k", "-c:s", "mov_text", "-metadata:s:s:0", "language=mon",
            "-metadata", "title=16:17 — Монгол төрийн түүхэн эргэлт (rough cut)", "-movflags", "+faststart",
            "-t", f"{total:.3f}", final])
    run(cmd)
    json.dump({"total_seconds": round(total, 3), "crossfade": XFADE, "opening": OPENING, "segments": timeline,
               "subtitle_cues": n_cues,
               "audio": {"narration_scenes": [s["scene"] for s in vo],
                         "narration_missing": [s["scene"] for s in timeline[1:] if not s.get("narration", {}).get("file")],
                         "music": "audio/music/score_ambient.wav (original, scripts/make_score.py), ducked",
                         "sfx": "scratch clock ticks (temporary)"}},
              open(os.path.join(OUT, "rough_cut_timeline.json"), "w"), ensure_ascii=False, indent=2)
    print(f"[1617] {final}: {total:.2f}s, {n_cues} subtitle cues")


if __name__ == "__main__":
    main()
