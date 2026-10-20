#!/usr/bin/env python3
"""Son Damla: müzik ve efektleri numpy ile sentezler (özgün, telifsiz).

Çıktı: assets/ses/sd_muzik.wav (60 sn), assets/ses/sd_efekt.wav (60 sn, zaman çizelgesine yerleşik).
Bölümler sd_assemble.sh'deki zaman çizelgesiyle aynıdır.
"""
import pathlib
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 48000
DUR = 60.0
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def piano(note, d, vel=0.5):
    t = t_(d)
    f = hz(note)
    s = sum(a * np.sin(2 * np.pi * f * k * t) for k, a in ((1, 1), (2, .45), (3, .2), (4, .1)))
    env = np.exp(-t * 2.8) * (1 - np.exp(-t * 400))
    return vel * s * env


def pad(notes, d, vel=0.12):
    t = t_(d)
    s = sum(np.sin(2 * np.pi * hz(n) * t) + .3 * np.sin(2 * np.pi * hz(n) * 2.003 * t) for n in notes)
    env = np.minimum(1, t / 0.8) * np.minimum(1, (d - t) / 0.8)
    return vel * s * env / len(notes)


def add(buf, sig, at):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def muzik():
    m = np.zeros(int(DUR * SR))
    # 0–6 sakin giriş: Am – F
    for at, ch in ((0, (57, 60, 64)), (3, (53, 57, 60))):
        add(m, pad(ch, 3.2), at)
        for k, n in enumerate((ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12)):
            add(m, piano(n, 1.5, .25), at + k * .75)
    # 6–20 gerilim: Am pedal, hızlanan sekizlikler, alçak davul
    t = 6.0
    while t < 20:
        prog = (t - 6) / 14
        step = 0.42 - 0.22 * prog
        n = (57, 60, 64, 65, 64, 60)[int(t / step) % 6] + 12
        add(m, piano(n, .6, .18 + .15 * prog), t)
        t += step
    for b in np.arange(6, 20, 1.0 - 0.0):
        tt = t_(.5)
        add(m, .5 * np.sin(2 * np.pi * (55 * np.exp(-tt * 6) + 40) * tt) * np.exp(-tt * 9), b)
    add(m, pad((45, 52, 57), 14.2, .16), 6)
    # 20–22 müzik durur (sağanak); 22–28 aydınlanma: tek notalar
    for k, n in enumerate((72, 76, 79, 84)):
        add(m, piano(n, 2.5, .22), 22.3 + k * 1.3)
    add(m, pad((60, 64, 67), 5.8, .08), 22.2)
    # 28–60 neşeli: C – G – Am – F, zıplayan bas + melodi
    prog = ((48, (60, 64, 67)), (43, (59, 62, 67)), (45, (60, 64, 69)), (41, (60, 65, 69)))
    mel = (76, 74, 72, 74, 76, 76, 76, None, 74, 74, 74, None, 76, 79, 79, None)
    bar = 2.0
    t, i = 28.0, 0
    while t < 58:
        bass, ch = prog[i % 4]
        add(m, pad(ch, bar + .2, .1), t)
        for k in range(4):
            add(m, piano(bass if k % 2 == 0 else bass + 12, .45, .3), t + k * .5)
            add(m, piano(ch[k % 3] + 12, .35, .12), t + k * .5 + .25)
        for k in range(4):
            n = mel[(i * 4 + k) % len(mel)]
            if n and t >= 40:
                add(m, piano(n, .6, .2), t + k * .5)
        t += bar
        i += 1
    # 56–60 fade-out
    fo = np.ones_like(m)
    a, b = int(56 * SR), int(60 * SR)
    fo[a:b] = np.linspace(1, 0, b - a)
    m *= fo
    return m


def gurultu(d):
    return rng.standard_normal(int(d * SR))


def lowpass(x, a):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def efekt():
    e = np.zeros(int(DUR * SR))
    # rüzgâr, gökyüzü (0–6)
    w = lowpass(gurultu(6), .02) * np.sin(np.pi * t_(6) / 6) * 1.2
    add(e, w, 0)
    # mercek: cızırtı ve ilk alev (6–11.5)
    cz = lowpass(gurultu(5.5), .3) * np.linspace(0, .25, int(5.5 * SR))
    add(e, cz, 6)
    # ateş çatırtısı (9–21)
    d = 12.0
    fire = lowpass(gurultu(d), .05) * .5
    for at in rng.uniform(0, d, 400):
        add(fire, gurultu(.006) * rng.uniform(.3, 1.0), at)
    env = np.minimum(1, t_(d) / 2) * np.minimum(1, (d - t_(d)) / 1.5)
    add(e, fire * env * .35, 9)
    # buhar tıslamaları (damlalar ateşe çarpıyor, 11.5–17; sağanak 20–24)
    for at in list(np.arange(11.8, 17, .55)) + list(np.arange(20.2, 24, .3)):
        h = gurultu(.5) - lowpass(gurultu(.5), .2)
        add(e, h * np.exp(-t_(.5) * 6) * .25, at)
    # yağmur (20–24)
    r = lowpass(gurultu(4.2), .5) * .12 * np.minimum(1, (4.2 - t_(4.2)) / 1)
    add(e, r, 20)
    # şişe yuvarlanma tıngırtısı (28–34) ve kutuya düşüş "şıngır" (36.5)
    for at in np.arange(28.4, 34, .7):
        tt = t_(.25)
        add(e, .12 * np.sin(2 * np.pi * rng.uniform(1800, 2600) * tt) * np.exp(-tt * 30), at)
    tt = t_(1.2)
    clink = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in ((2350, 6), (3700, 9), (5200, 14)))
    add(e, .25 * clink, 36.5)
    # kuşlar (40–52)
    for at in (40.6, 41.1, 43.8, 47.2, 47.5, 50.3):
        tt = t_(.18)
        f = 3200 + 1600 * np.sin(np.pi * tt / .18)
        add(e, .08 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / .18), at)
    # damla düşüşü "plip" (52.8)
    tt = t_(.35)
    f = 700 + 1500 * tt / .35
    add(e, .3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 14), 52.8)
    return e


def yaz(path, x, peak=.8):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    st = np.repeat((x * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


if __name__ == "__main__":
    yaz(ROOT / "assets/ses/sd_muzik.wav", muzik(), .7)
    yaz(ROOT / "assets/ses/sd_efekt.wav", efekt(), .8)
    print("assets/ses/sd_muzik.wav, assets/ses/sd_efekt.wav yazıldı")
