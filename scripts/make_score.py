#!/usr/bin/env python3
"""Original ambient score for 16:17, synthesised from scratch with numpy
(no samples, no third-party music, so the project owns it).

    python3 scripts/make_score.py [seconds]   -> audio/music/score_ambient.wav

Slow D-minor pad (Dm - Bb - F - C) over a low D/A drone, soft attacks,
gentle low-pass and a light echo room (FFmpeg). It is mixed at low level
and ducked under the narration by scripts/assemble_rough.py.
"""
import os
import sys
import wave

import numpy as np

SR = 48000
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def note(f, t, detune=0.0):
    ph = 2 * np.pi * f * (1 + detune) * t
    return np.sin(ph) + 0.35 * np.sin(2 * ph + 0.3) + 0.12 * np.sin(3 * ph + 1.1)


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 250.0
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    # drone D2 + A2 with very slow swell
    sw = 0.6 + 0.4 * np.sin(2 * np.pi * t / 37.0)
    for f, g in ((73.42, 0.22), (110.0, 0.14), (146.83, 0.06)):
        d = note(f, t) * g * sw
        out[:, 0] += d
        out[:, 1] += note(f, t, 0.0015) * g * sw
    # chord pads, 12 s each, crossfaded
    chords = [(146.83, 174.61, 220.0), (116.54, 146.83, 174.61), (174.61, 220.0, 261.63), (130.81, 164.81, 196.0)]
    seg = 12.0
    for k in range(int(dur // seg) + 2):
        c = chords[k % len(chords)]
        a = k * seg - 2.0
        i0, i1 = max(0, int(a * SR)), min(n, int((a + seg + 4.0) * SR))
        if i0 >= n:
            break
        tt = t[i0:i1] - a
        env = np.clip(tt / 4.0, 0, 1) * np.clip((seg + 4.0 - tt) / 4.0, 0, 1)
        env = env * env * (3 - 2 * env)
        for j, f in enumerate(c):
            g = 0.07 / (1 + j * 0.3)
            out[i0:i1, 0] += note(f, t[i0:i1], -0.002 * j) * g * env
            out[i0:i1, 1] += note(f, t[i0:i1], 0.002 * j) * g * env
    # fades and normalisation (peak -6 dBFS; final level is set in the mix)
    fade = int(6 * SR)
    out[:fade] *= np.linspace(0, 1, fade)[:, None]
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out /= np.max(np.abs(out)) / 0.5
    path = os.path.join(ROOT, "audio", "music", "score_ambient.wav")
    raw = path.replace(".wav", "_dry.wav")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())
    # warmth (low-pass) + light room (echo) with FFmpeg
    import subprocess
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af",
                    "lowpass=f=1600,aecho=0.8:0.6:370|530:0.30|0.22,volume=0.8", path], check=True)
    os.remove(raw)
    print(path, f"{dur:.1f}s")


if __name__ == "__main__":
    main()
