#!/usr/bin/env python3
"""Verify the eight ElevenLabs narration files and align the script to them.

    python3 scripts/narration.py            # writes output/narration_alignment.json

Input : audio/narration/sceneNN.mp3 (or .wav), one per scene, generated with
        ElevenLabs Eleven v4, voice "Bilguun", text = 08_voiceover_paste_ready/scene_NN.txt
        (identical to 02_narration_mn.md).
Checks: real audio stream (ffprobe), duration > 1 s.
Align : sentence boundaries are taken from the actual pauses in the audio
        (FFmpeg silencedetect), choosing the pauses that best match the expected
        positions by dynamic programming. Long sentences are split into <=2-line
        cues inside their measured span. This replaces text-length-only timing.
Scenes without a verified file are reported as missing (no fake timing is
written for them).
"""
import json
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUDIO = os.path.join(ROOT, "audio", "narration")
TEXT = os.path.join(ROOT, "docs", "director_pack", "08_voiceover_paste_ready")
SCENES = [f"{i:02d}" for i in range(1, 9)]


def ffprobe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                        "stream=codec_name,sample_rate,channels:format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    j = json.loads(r.stdout)
    if not j.get("streams"):
        return None
    return {"codec": j["streams"][0]["codec_name"], "duration": float(j["format"]["duration"]),
            "sample_rate": int(j["streams"][0]["sample_rate"]), "channels": j["streams"][0]["channels"]}


def silences(path, noise="-35dB", d=0.18):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=noise={noise}:d={d}",
                        "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def sentences(text):
    return [p.strip() for p in re.split(r"(?<=[.?!])\s+", text.strip()) if p.strip()]


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


def align(path, text):
    info = ffprobe(path)
    dur = info["duration"]
    sil = silences(path)
    lead = sil[0][1] if sil and sil[0][0] < 0.05 and sil[0][1] else 0.0
    tail = sil[-1][0] if sil and sil[-1][1] is None else dur
    inner = [(a, b) for a, b in sil if b is not None and a > lead + 0.1 and b < tail - 0.1]
    sents = sentences(text)
    n = len(sents)
    chars = [len(s) for s in sents]
    speech = tail - lead
    expected = []
    acc = 0
    for c in chars[:-1]:
        acc += c
        expected.append(lead + speech * acc / sum(chars))
    # DP: pick n-1 increasing pauses minimising distance to expected boundaries, favouring long pauses
    m = len(inner)
    INF = 1e9
    if m >= n - 1 and n > 1:
        cost = [[INF] * (m + 1) for _ in range(n)]
        back = [[-1] * (m + 1) for _ in range(n)]
        for j in range(m + 1):
            cost[0][j] = 0.0
        for k in range(1, n):
            for j in range(k, m + 1):
                a, b = inner[j - 1]
                mid = (a + b) / 2
                c = abs(mid - expected[k - 1]) / max(1.0, speech) * 10 - (b - a)
                best, arg = INF, -1
                for i in range(k - 1, j):
                    if cost[k - 1][i] < best:
                        best, arg = cost[k - 1][i], i
                cost[k][j] = best + c
                back[k][j] = arg
        j = min(range(n - 1, m + 1), key=lambda jj: cost[n - 1][jj])
        picks = []
        for k in range(n - 1, 0, -1):
            picks.append(inner[j - 1])
            j = back[k][j]
        picks.reverse()
        method = "silence-aligned"
    else:
        picks = [(e - 0.05, e + 0.05) for e in expected]
        method = "proportional (too few pauses detected)"
    bounds = [lead] + [x for p in picks for x in p] + [tail]
    spans = [(bounds[2 * i], bounds[2 * i + 1]) for i in range(n)]
    cues = []
    for s, (a, b) in zip(sents, spans):
        lines = wrap(s)
        chunks = ["\n".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]
        tot = sum(len(c) for c in chunks)
        t = a
        for c in chunks:
            d = (b - a) * len(c) / tot
            cues.append({"start": round(t, 3), "end": round(t + d, 3), "text": c})
            t += d
    return {"file": os.path.relpath(path, ROOT), "audio": info, "speech_start": round(lead, 3),
            "speech_end": round(tail, 3), "sentences": n, "method": method,
            "sentence_spans": [[round(a, 3), round(b, 3)] for a, b in spans], "cues": cues}


def main():
    report = {"voice": "ElevenLabs Eleven v4 · Bilguun (calm narration, mn)", "scenes": {}, "missing": []}
    for s in SCENES:
        path = next((os.path.join(AUDIO, f"scene{s}.{ext}") for ext in ("wav", "mp3")
                     if os.path.exists(os.path.join(AUDIO, f"scene{s}.{ext}"))), None)
        text = open(os.path.join(TEXT, f"scene_{s}.txt"), encoding="utf-8").read()
        info = ffprobe(path) if path else None
        if not info or info["duration"] < 1.0:
            report["missing"].append(s)
            continue
        report["scenes"][s] = align(path, text)
        a = report["scenes"][s]
        print(f"scene {s}: {a['audio']['duration']:.2f}s, {a['sentences']} sentences, {a['method']}")
    out = os.path.join(ROOT, "output", "narration_alignment.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("missing:", report["missing"] or "none", "->", out)


if __name__ == "__main__":
    main()
