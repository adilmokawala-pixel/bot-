"""Synthesize the Mokawala SFX + music library into public/sfx/*.wav.

Everything is generated procedurally (numpy), so the library is reproducible
and has no licensing issues. Run once: python3 scripts/sfx.py
"""
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "public" / "sfx"
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a, r, curve=3.0):
    """Attack/release envelope over n samples (a, r in seconds)."""
    e = np.ones(n)
    na, nr = int(SR * a), int(SR * r)
    if na:
        e[:na] = np.linspace(0, 1, na) ** 2
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e


def bandnoise(n, lo, hi):
    """Noise band-limited in the frequency domain (lo/hi arrays or scalars, Hz)."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(spec, n)


def sweep_noise(d, f0, f1, q=0.35):
    """Noise through a moving band-pass (whoosh core), frame by frame."""
    n = int(SR * d)
    hop = 512
    out = np.zeros(n + hop * 2)
    win = np.hanning(hop * 2)
    frames = n // hop + 1
    for i in range(frames):
        x = i / max(frames - 1, 1)
        fc = f0 * (f1 / f0) ** x
        seg = bandnoise(hop * 2, fc * (1 - q), fc * (1 + q)) * win
        out[i * hop:i * hop + hop * 2] += seg
    return out[:n]


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def stereo(x, width=0.0):
    if width:
        d = int(SR * 0.0007)
        r = np.concatenate([np.zeros(d), x[:-d]])
        return np.stack([x, x * (1 - width) + r * width], 1)
    return np.stack([x, x], 1)


def save(name, x, width=0.0):
    OUT.mkdir(parents=True, exist_ok=True)
    sf.write(OUT / f"{name}.wav", stereo(norm(x), width), SR, subtype="PCM_16")


def whoosh():
    d = 0.55
    n = int(SR * d)
    core = sweep_noise(d, 300, 4200)
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    body = np.sin(2 * np.pi * np.cumsum(np.linspace(90, 45, n)) / SR) * 0.25
    return (core * shape + body * shape) * env(n, 0.01, 0.2)


def swipe():
    d = 0.18
    n = int(SR * d)
    return sweep_noise(d, 1800, 6500, 0.25) * np.sin(np.linspace(0, np.pi, n)) ** 2


def pop():
    d = 0.14
    x = t(d)
    f = 520 * np.exp(-x * 22) + 260
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 38)
    click = bandnoise(len(x), 2000, 9000) * np.exp(-x * 400) * 0.35
    return tone + click


def check():
    d = 0.32
    x = t(d)
    a = np.sin(2 * np.pi * 1318.5 * x) * np.exp(-x * 18)
    b = np.sin(2 * np.pi * 1975.5 * x) * np.exp(-np.clip(x - 0.07, 0, None) * 16) * (x > 0.07)
    return (a + b * 0.8) * env(len(x), 0.002, 0.08)


def shimmer():
    d = 0.9
    x = t(d)
    out = np.zeros_like(x)
    for i, f in enumerate([1568, 2093, 2637, 3136, 3951, 4186]):
        st = i * 0.05
        m = x >= st
        xx = np.clip(x - st, 0, None)
        out += np.sin(2 * np.pi * f * xx) * np.exp(-xx * 5) * m * (0.9 ** i)
    air = bandnoise(len(x), 6000, 14000) * np.exp(-x * 4) * 0.25
    return (out + air) * env(len(x), 0.005, 0.3)


def typing():
    d = 1.6
    n = int(SR * d)
    out = np.zeros(n)
    pos = 0.02
    while pos < d - 0.05:
        k = int(pos * SR)
        L = int(SR * 0.03)
        xx = np.arange(L) / SR
        click = bandnoise(L, 1500, 7000) * np.exp(-xx * 260)
        click += np.sin(2 * np.pi * rng.uniform(180, 260) * xx) * np.exp(-xx * 120) * 0.4
        out[k:k + L] += click * rng.uniform(0.6, 1.0)
        pos += rng.uniform(0.07, 0.14)
    return out


def notif():
    d = 0.55
    x = t(d)
    a = np.sin(2 * np.pi * 880 * x) * np.exp(-x * 9) * (x < 0.2)
    xb = np.clip(x - 0.12, 0, None)
    b = np.sin(2 * np.pi * 1318.5 * xb) * np.exp(-xb * 7) * (x >= 0.12)
    return (a + b) * env(len(x), 0.003, 0.15)


def impact():
    d = 1.4
    x = t(d)
    f = 150 * np.exp(-x * 9) + 42
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 3.2)
    hit = bandnoise(len(x), 60, 3000) * np.exp(-x * 30) * 0.6
    tail = bandnoise(len(x), 200, 1500) * np.exp(-x * 4) * 0.12
    return np.tanh((boom + hit + tail) * 1.6)


def swell():
    d = 2.2
    n = int(SR * d)
    x = t(d)
    pad = sum(np.sin(2 * np.pi * f * x) for f in (110, 164.8, 220, 329.6)) / 4
    noise = bandnoise(n, 300, 2500) * 0.25
    rise = (x / d) ** 2.2
    return (pad + noise) * rise * env(n, 0.0, 0.12)


def air():
    d = 0.7
    n = int(SR * d)
    core = sweep_noise(d, 5000, 900, 0.4)
    return core * np.sin(np.linspace(0, np.pi, n)) ** 2


def music():
    """Warm minimal loop at 95 BPM, 8 bars (Am - F - C - G)."""
    bpm = 95
    beat = 60 / bpm
    bars = 8
    d = bars * 4 * beat
    n = int(SR * d)
    out = np.zeros(n)
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    for bar in range(bars):
        ch = chords[bar % 4]
        st = int(bar * 4 * beat * SR)
        L = int(4 * beat * SR)
        xx = np.arange(L) / SR
        e = env(L, 0.25, 0.6, 2)
        pad = sum(np.sin(2 * np.pi * hz(m) * xx) + 0.3 * np.sin(2 * np.pi * hz(m) * 2.003 * xx) for m in ch) / 3
        bass = np.sin(2 * np.pi * hz(ch[0] - 12) * xx) * 0.6
        out[st:st + L] += (pad * 0.5 + bass * 0.5) * e
        for b in range(4):
            k = st + int(b * beat * SR)
            Lk = int(0.25 * SR)
            xk = np.arange(Lk) / SR
            kick = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-xk * 30) + 45) / SR) * np.exp(-xk * 14)
            out[k:k + Lk] += kick * (0.55 if b % 2 == 0 else 0.3)
            h = k + int(beat / 2 * SR)
            Lh = int(0.05 * SR)
            if h + Lh < n:
                out[h:h + Lh] += bandnoise(Lh, 7000, 14000) * np.exp(-np.arange(Lh) / SR * 90) * 0.12
    # soft low-pass for warmth
    spec = np.fft.rfft(out)
    f = np.fft.rfftfreq(n, 1 / SR)
    spec *= 1 / (1 + (f / 3500) ** 2)
    return np.fft.irfft(spec, n)


if __name__ == "__main__":
    for name, fn, w in [
        ("whoosh", whoosh, 0.4), ("swipe", swipe, 0.3), ("pop", pop, 0), ("check", check, 0),
        ("shimmer", shimmer, 0.5), ("typing", typing, 0), ("notif", notif, 0), ("impact", impact, 0.2),
        ("swell", swell, 0.5), ("air", air, 0.5), ("music", music, 0.3),
    ]:
        save(name, fn(), w)
        print("wrote", name)
