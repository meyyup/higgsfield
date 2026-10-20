#!/usr/bin/env python3
"""Ekran yazıları, yıl sayacı, kar efekti ve hayal maskesi (PIL).

Çıktılar (work/overlays/):
  katman.mov        60 sn, 25 fps, RGBA (qtrle) — tüm yazı/sayaç/kar katmanı, ffmpeg overlay ile basılır
  kart_*.png        tek tek yazı kartları (şeffaf PNG; tanıtım ve kontrol için)
  hayal_maske.png   hayal filtresi kenar bulanıklığı maskesi (kenarlar beyaz)
Türkçe karakterler her çalıştırmada fontta var mı diye test edilir.
"""
import math
import pathlib
import random
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "overlays"
CMD_LOG = ROOT / "out" / "komutlar.log"
W, H, FPS, DUR = 1920, 1080, 25, 60.0
INTER = "/usr/share/fonts/opentype/inter/"
F_TITLE = INTER + "InterDisplay-Bold.otf"
F_SEMI = INTER + "Inter-SemiBold.otf"
F_REG = INTER + "Inter-Regular.otf"
FADE = 0.4

# (ad, metin, font, punto, merkez_y, başla, bitir, harf_aralığı)
CARDS = [
    ("baslik", "±1°C", F_TITLE, 210, 735, 0.0, 3.0, 0),
    ("baslik_alt", "BİR DERECE", F_SEMI, 46, 868, 0.0, 3.0, 14),
    ("ben_ela", "Ben Ela.", F_SEMI, 68, 860, 3.0, 6.0, 0),
    ("dunya", "Dünya yaklaşık 1 derece ısındı.", F_SEMI, 58, 880, 14.0, 20.0, 0),
    ("eksi2", "–2", F_TITLE, 150, 820, 26.2, 28.0, 0),
    ("eksi1_kis", "–1 kış", F_TITLE, 120, 830, 45.3, 49.0, 0),
    ("arti1_yaz", "+1 yaz", F_TITLE, 120, 830, 49.3, 54.0, 0),
    ("kapanis1", "Büyük değişiklikler küçük hareketlerle başlar.", F_SEMI, 54, 760, 54.4, 60.0, 0),
    ("kapanis2", "İleriyi düşün. Sen de 1 derece katkı ver.", F_SEMI, 54, 840, 56.0, 60.0, 0),
    ("kapanis3", "Kışın kombiyi 1 derece kıs, yazın klimayı 1 derece aç.", F_REG, 32, 915, 57.2, 60.0, 0),
    ("talentcup", "TalentCup-2026", F_SEMI, 30, 1000, 57.6, 60.0, 4),
]
# yıl sayacı: (başla, bitir, yıl_başı, yıl_sonu) parçaları; montajdaki klip sınırlarıyla aynı
COUNTER = [
    (8.0, 13.5, 2026, 2040), (13.5, 14.5, 2040, 2055), (14.5, 20.0, 2055, 2076),
    (30.0, 35.5, 2026, 2040), (35.5, 36.5, 2040, 2055), (36.5, 42.0, 2055, 2076),
]
SNOW = (54.0, 60.0, (904, 0, 1530, 665))  # başla, bitir, pencere camı kutusu
TR_CHARS = "çÇğĞıİöÖşŞüÜ±°–"


def check_glyphs():
    """Fontta eksik glif (tofu) var mı? Eksik glif, bilinen yok karakterle aynı çizilir."""
    bad = []
    for path in {c[2] for c in CARDS}:
        font = ImageFont.truetype(path, 80)
        missing = font.getmask("\U000F0000").getbbox()
        for ch in TR_CHARS:
            m = font.getmask(ch)
            if m.getbbox() is None or (m.getbbox() == missing and bytes(m) == bytes(font.getmask("\U000F0000"))):
                bad.append((pathlib.Path(path).name, ch))
    if bad:
        sys.exit(f"Türkçe karakter testi KALDI: {bad}")
    print(f"Türkçe karakter testi geçti ({TR_CHARS})")


def text_layer(text, font_path, size, cy, tracking=0, cx=W // 2, anchor="m"):
    font = ImageFont.truetype(font_path, size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if tracking:
        widths = [font.getlength(c) + tracking for c in text]
        x = cx - (sum(widths) - tracking) / 2
        for c, w in zip(text, widths):
            d.text((x, cy), c, font=font, fill="white", anchor="lm")
            x += w
    else:
        d.text((cx, cy), text, font=font, fill="white", anchor=anchor + "m")
    alpha = layer.getchannel("A")
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(max(3, size // 14))).point(lambda v: int(v * 0.65)))
    shadow = ImageChops.offset(shadow, 2, 3)
    return Image.alpha_composite(shadow, layer)


def fade(t, a, b):
    if t < a or t >= b:
        return 0.0
    return min(1.0, (t - a) / FADE, (b - t) / FADE if b < DUR else 1.0)


def with_alpha(img, k):
    if k >= 0.999:
        return img
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: int(v * k)))
    return out


def year_at(t):
    for a, b, y0, y1 in COUNTER:
        if a <= t < b:
            return int(round(y0 + (y1 - y0) * (t - a) / (b - a))), fade(t, COUNTER[0][0] if a < 21 else 30.0,
                                                                         20.0 if a < 21 else 42.0)
    return None, 0.0


def snow_flakes(n=170, seed=7):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = SNOW[2]
    return [(rnd.uniform(x0, x1), rnd.uniform(y0 - 700, y1), rnd.uniform(2, 6), rnd.uniform(40, 110),
             rnd.uniform(0, 6.28), rnd.uniform(0.5, 1.0)) for _ in range(n)]


def snow_frame(t, flakes):
    x0, y0, x1, y1 = SNOW[2]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    dt = t - SNOW[0]
    k = fade(t, SNOW[0], SNOW[1])
    for fx, fy, r, speed, ph, op in flakes:
        y = y0 + ((fy - y0 + speed * dt) % (y1 - y0 + 700)) - 350
        x = fx + 14 * math.sin(ph + dt * 1.3)
        if x0 <= x <= x1 and y0 <= y <= y1:
            a = int(230 * op * k)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
    return layer.filter(ImageFilter.GaussianBlur(1.2))


def dream_mask():
    """Merkez siyah (keskin), kenarlar beyaz (bulanık); yumuşak radyal geçiş."""
    small = Image.new("L", (192, 108))
    px = small.load()
    for y in range(108):
        for x in range(192):
            r = math.hypot((x - 96) / 96, (y - 54) / 54)
            px[x, y] = int(255 * max(0.0, min(1.0, (r - 0.55) / 0.5)))
    return small.resize((W, H), Image.BICUBIC)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    check_glyphs()
    dream_mask().save(OUT / "hayal_maske.png")
    cards = {}
    for name, txt, fp, size, cy, a, b, tr in CARDS:
        cards[name] = (text_layer(txt, fp, size, cy, tr), a, b)
        cards[name][0].save(OUT / f"kart_{name}.png")
    year_font = (F_TITLE, 76)
    year_cache = {}
    flakes = snow_flakes()

    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb", str(OUT / "katman.mov")]
    with CMD_LOG.open("a", encoding="utf-8") as f:
        f.write("ffmpeg " + " ".join(cmd[1:]) + "  # stdin: overlays.py RGBA kareleri\n")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    last_key, last_bytes = None, None
    for i in range(int(DUR * FPS)):
        t = i / FPS
        parts = [(n, round(fade(t, a, b), 2)) for n, (img, a, b) in cards.items() if fade(t, a, b) > 0]
        year, yk = year_at(t)
        key = (tuple(parts), year, round(yk, 2), SNOW[0] <= t < SNOW[1] and i)
        if key != last_key:
            frame = blank.copy()
            for n, k in parts:
                frame = Image.alpha_composite(frame, with_alpha(cards[n][0], k))
            if year:
                if year not in year_cache:
                    year_cache[year] = text_layer(str(year), *year_font, cy=95, cx=W - 90, anchor="r")
                frame = Image.alpha_composite(frame, with_alpha(year_cache[year], yk))
            if SNOW[0] <= t < SNOW[1]:
                frame = Image.alpha_composite(frame, snow_frame(t, flakes))
            last_key, last_bytes = key, frame.tobytes()
        proc.stdin.write(last_bytes)
    proc.stdin.close()
    if proc.wait():
        sys.exit("katman.mov yazılamadı")
    print(f"overlays: {len(cards)} kart, katman.mov ({DUR:.0f} sn)")


if __name__ == "__main__":
    main()
