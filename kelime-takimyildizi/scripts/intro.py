#!/usr/bin/env python3
"""Giriş videosu (kapaktaki QR): shorts/00_giris_<varyant>.mp4 — 1080×1920, 30 fps, H.264 + AAC, müzik yok.

Ses iki adımda hazırlanır; montaj, ses parçalarının sürelerine göre sahneleri kendisi dizer:
  python3 scripts/intro.py ses-yz            # ElevenLabs (kart sesiyle aynı), 5 cümle → work/intro/yz/
  python3 scripts/intro.py montaj yz         # → shorts/00_giris_yz.mp4

Mert'in sesiyle: her cümle ayrı dosya olarak work/intro/mert/01.m4a … 05.m4a (ya da tek kayıt, sonra bölünür)
konur, `python3 scripts/intro.py ses-dosya mert` ile zaman bilgisi çıkarılır, ardından `montaj mert`.
"""
import base64
import json
import math
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cover as C  # noqa: E402
import re

ROOT = C.ROOT
W, H, FPS = 1080, 1920, 30
LEAD, GAP, TAIL = 0.8, 0.7, 3.2           # açılış sessizliği, cümle arası, kapanış kartı
SCENES_YZ = [
    "Gökyüzünde her yıldızın bir adı vardır; dilimizde de her kelimenin bir hikâyesi.",
    "Bu sözlükte, Türkçenin otuz güzel kelimesi üç takımyıldızda toplandı: Kültürümüz, Eski Sözcükler ve Değerler.",
    "Her kartta kelimenin anlamını, bir örnek cümleyi ve küçük bir bilgiyi bulacaksınız.",
    "Kartın köşesindeki QR kodu okutun; kelime size kendini anlatsın.",
    "Her kelime bir yıldız, her yıldız bir kelime. Haydi, Türkçenin yıldızlarını birlikte keşfedelim!",
]
SCENES_MERT = SCENES_YZ[:1] + [
    "Bu sözlükte, Türkçenin otuz güzel kelimesini üç takımyıldızda topladım: Kültürümüz, Eski Sözcükler ve Değerler.",
] + SCENES_YZ[2:]


def chunks(text, maxw=7):
    """Altyazı parçaları: noktalama (, ; : . ! ?) sınırlarından böl, kısa parçaları en çok 7 kelimeye kadar birleştir."""
    parts = [(m.start(), m.end()) for m in re.finditer(r"[^,;:.!?]+[,;:.!?]*", text) if m.group().strip()]
    out, cur = [], None
    for a, b in parts:
        a += len(text[a:b]) - len(text[a:b].lstrip())
        if cur and text[cur[0]:cur[1]].rstrip()[-1] not in ".!?" and len(text[cur[0]:b].split()) <= maxw:
            cur = (cur[0], b)
        else:
            if cur:
                out.append(cur)
            cur = (a, b)
    out.append(cur)
    return out


def work(variant):
    p = ROOT / "work" / "intro" / variant
    p.mkdir(parents=True, exist_ok=True)
    return p


def dur(p):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


# ------------------------------------------------------------------ ses
def ses_yz():
    import tts as T
    wd = work("yz")
    segs = []
    for i, text in enumerate(SCENES_YZ):
        r = T.tts(text, 0.95, prev=SCENES_YZ[i - 1] if i else None,
                  nxt=SCENES_YZ[i + 1] if i + 1 < len(SCENES_YZ) else None)
        mp3 = wd / f"{i + 1:02d}.mp3"
        mp3.write_bytes(base64.b64decode(r["audio_base64"]))
        al = r["alignment"]
        segs.append({"text": text, "file": mp3.name, "dur": dur(mp3),
                     "chars": al["characters"], "start": al["character_start_times_seconds"],
                     "end": al["character_end_times_seconds"]})
        print(f"{i + 1}: {segs[-1]['dur']:.2f} sn")
    meta = {"model": T.MODEL, "voice_id": T.VOICE_ID, "segments": segs}
    (wd / "segments.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


# ------------------------------------------------------------------ çizim yardımcıları
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


OPENING = ROOT / "cover" / "giris" / "kitap_acilis.mp4"   # Higgsfield: çocuk kitabı açar, yıldızlar yükselir


class Opening:
    """Açılış videosunu kare kare okur (sıralı erişim); bittiğinde None döner."""

    def __init__(self):
        self.size = (W + 68, H + 120)
        self.proc = None
        if OPENING.exists():
            self.dur = dur(OPENING)
            self.proc = subprocess.Popen(
                ["ffmpeg", "-v", "error", "-i", str(OPENING), "-vf",
                 f"fps={FPS},scale={self.size[0]}:{self.size[1]}:flags=lanczos", "-f", "rawvideo",
                 "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None

    def frame(self):
        if not self.proc:
            return None
        raw = self.proc.stdout.read(self.size[0] * self.size[1] * 3)
        if len(raw) < self.size[0] * self.size[1] * 3:
            self.proc = None
            return None
        self.last = Image.frombytes("RGB", self.size, raw)
        return self.last


def bg_base():
    src = Image.open(ROOT / "cover" / "giris" / "bitis.png").convert("RGB")   # açılış videosunun son karesi
    s = (H + 120) / src.height                       # yakınlaşma payı
    im = src.resize((round(src.width * s), H + 120), Image.LANCZOS)
    x0 = (im.width - (W + 68)) // 2
    return im.crop((x0, 0, x0 + W + 68, H + 120))


def bg_frame(base, t, total):
    z = 1.0 + 0.04 * (t / total)                     # çok yavaş yakınlaşma
    w, h = round(W * z), round(H * z)
    im = base.resize((w + 68 * w // W, h + 120 * h // H), Image.BILINEAR)
    x = (im.width - W) // 2
    y = im.height - H - round(40 * (1 - t / total))  # hafif yukarı kayma
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def text_layer(lines):
    """[(xy, text, font, fill, anchor)] → RGBA katman (gölgeli)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds, d = ImageDraw.Draw(sh), ImageDraw.Draw(img)
    for xy, text, f, fill, anchor in lines:
        ds.text((xy[0] + 3, xy[1] + 4), text, font=f, fill=(0, 0, 15, 200), anchor=anchor)
        d.text(xy, text, font=f, fill=fill, anchor=anchor)
    out = sh.filter(ImageFilter.GaussianBlur(6))
    out.alpha_composite(img)
    return out


def fade(layer, a):
    if a >= 0.999:
        return layer
    out = layer.copy()
    out.putalpha(out.getchannel("A").point(lambda v: int(v * a)))
    return out


# takımyıldızlar: kapak koordinatlarından videoya
CS, CX0, CY0, CY1 = 0.66, 874, 740, 610           # kapak (874, 740) → video (540, 610)


def cv(x, y):
    return (x - CX0) * CS + W / 2, (y - CY0) * CS + CY1


def stars_layers(words):
    """Yıldızlar sırayla yanar: layers[k] = ilk k yıldızın çizili olduğu katman (k = 0…30)."""
    order = [(cat, i) for cat in C.CATS for i in range(10)]
    fw = C.font(C.SERIF_I, 40)
    fl = C.font(C.SANS_B, 20)
    layers = [Image.new("RGBA", (W, H), (0, 0, 0, 0))]
    for k in range(1, len(order) + 1):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vis = set(order[:k])
        for cat, color in C.CATS.items():
            lay = C.LAYOUT[cat]
            pts = [cv(x, y) + (side,) for x, y, side in lay["pts"]]
            line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(line)
            for a, b in lay["edges"]:
                if (cat, a) in vis and (cat, b) in vis:
                    ld.line([pts[a][:2], pts[b][:2]], fill=color + (160,), width=3)
            img.alpha_composite(line)
            d = ImageDraw.Draw(img)
            for i, (x, y, side) in enumerate(pts):
                if (cat, i) not in vis:
                    continue
                big = i == 0
                C.glow(img, x, y, 24 if big else 14, color, 130 if big else 100)
                r = 9 if big else 6
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)
                d.ellipse([x - r / 2.5, y - r / 2.5, x + r / 2.5, y + r / 2.5], fill=(255, 250, 235))
                off = 16
                tx, ty, anchor = {"b": (x, y - off, "md"), "t": (x, y + off, "ma"),
                                  "l": (x + off, y, "lm"), "r": (x - off, y, "rm")}[side]
                d.text((tx + 2, ty + 2), words[cat][i], font=fw, fill=(0, 0, 20), anchor=anchor)
                d.text((tx, ty), words[cat][i], font=fw, fill=color, anchor=anchor)
            if (cat, 0) in vis:
                lx, ly = cv(*lay["label"])
                C.spaced(d, (lx, ly), cat.replace("i", "İ").upper(), fl, color, 5)
        layers.append(img)
    return layers


def card_sprite(nn, width, angle=0):
    card = Image.open(ROOT / "cards" / "png" / f"{nn}.png").convert("RGBA")
    card = card.resize((width, round(card.height * width / card.width)), Image.LANCZOS)
    pad = 40
    sp = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", sp.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad + 6, pad + 12, pad + card.width + 6, pad + card.height + 12], fill=(0, 0, 0, 140))
    sp.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    sp.alpha_composite(card, (pad, pad))
    return sp.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else sp


def phone_sprite(screen):
    pw, ph = 330, 640
    ph_img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(ph_img)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=48, fill=(25, 25, 32, 255))
    sw, shh = pw - 36, ph - 90
    scr = screen.resize((sw, shh), Image.LANCZOS)
    m = Image.new("L", (sw, shh), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, shh - 1], radius=30, fill=255)
    ph_img.paste(scr, (18, 45), m)
    d.rounded_rectangle([pw // 2 - 45, 16, pw // 2 + 45, 28], radius=6, fill=(60, 60, 70, 255))
    return ph_img


def subtitle_layer(text):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = C.font(C.F / "NotoSans-Bold.ttf", 52)
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) > W - 160 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    lh, cy = 70, 1770
    top, bot = cy - lh * len(lines) / 2 - 22, cy + lh * len(lines) / 2 + 22
    d.rounded_rectangle([50, top, W - 50, bot], radius=26, fill=(0, 0, 0, 150))
    for i, ln in enumerate(lines):
        d.text((W // 2, cy - lh * (len(lines) - 1) / 2 + i * lh), ln, font=f, fill="white", anchor="mm")
    return img


# ------------------------------------------------------------------ montaj
def montaj(variant):
    wd = work(variant)
    meta = json.loads((wd / "segments.json").read_text(encoding="utf-8"))
    segs = meta["segments"]
    # zaman çizelgesi
    t, times = LEAD, []
    for s in segs:
        times.append((t, t + s["dur"]))
        t += s["dur"] + GAP
    total = t - GAP + TAIL
    print(f"süre: {total:.2f} sn")

    # ses: parçaları zaman çizelgesine yerleştir
    inputs, filt = [], []
    for i, (s, (a, _)) in enumerate(zip(segs, times)):
        inputs += ["-i", str(wd / s["file"])]
        filt.append(f"[{i}:a]aresample=48000,adelay={int(a * 1000)}:all=1[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(segs))) +
                f"amix=inputs={len(segs)}:normalize=0,apad,atrim=duration={total:.3f},"
                "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
    audio = wd / "ses.m4a"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "[a]", "-c:a", "aac", "-b:a", "160k", str(audio)], check=True)

    # altyazı parçaları (karakter zaman damgaları varsa onlarla, yoksa süreye orantılı)
    subs = []
    for s, (a, b) in zip(segs, times):
        text = s["text"]
        for ca, cb in chunks(text):
            if s.get("start") and "".join(s["chars"]) == text:
                st, en = a + s["start"][ca], a + s["end"][cb - 1]
            else:
                st, en = a + (b - a) * ca / len(text), a + (b - a) * cb / len(text)
            subs.append([text[ca:cb], st, en])
    for i in range(len(subs) - 1):
        if subs[i + 1][1] - subs[i][2] < 0.8:
            subs[i][2] = subs[i + 1][1]
    sub_layers = [subtitle_layer(x[0]) for x in subs]

    rows = [r for r in __import__("csv").DictReader((ROOT / "kelimeler.csv").open(encoding="utf-8"))]
    words = {c: [r["kelime"] for r in rows if r["kategori"] == c] for c in C.CATS}
    base = bg_base()
    title = text_layer([((W // 2, 210), "TÜRKÇENİN", C.font(C.SERIF, 128), C.CREAM, "mm"),
                        ((W // 2, 345), "YILDIZLARI", C.font(C.SERIF, 128), C.CREAM, "mm")])
    subtitle = text_layer([((W // 2, 445), "Üç Takımyıldız, Otuz Kelime", C.font(C.SERIF_I, 58), C.GOLD, "mm")])
    stars = stars_layers(words)
    dim = Image.new("RGBA", (W, H), (5, 10, 35, 150))
    cards = [("01", -9, 285), ("11", 0, 540), ("21", 9, 795)]
    card_sp = {nn: card_sprite(nn, 470, ang) for nn, ang, _ in cards}
    big = card_sprite("01", 760)
    # telefon ekranları: kamera görüntüsü (kartın QR bölgesi) ve İmece videosundan bir kare
    card_full = Image.open(ROOT / "cards" / "png" / "01.png").convert("RGB")
    cam = card_full.crop((1748 - 96 - 295 - 260, 2480 - 96 - 295 - 400, 1748 - 40, 2480 - 40))
    vid = ROOT / "work" / "intro" / "imece_kare.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "6", "-i", str(ROOT / "shorts" / "01_imece.mp4"),
                    "-frames:v", "1", str(vid)], check=True)
    vid_img = Image.open(vid).convert("RGB")
    vd = ImageDraw.Draw(vid_img)
    vd.ellipse([540 - 110, 960 - 110, 540 + 110, 960 + 110], fill=(0, 0, 0))
    vd.polygon([(510, 905), (510, 1015), (605, 960)], fill="white")
    phone_cam = phone_sprite(cam)
    phone_vid = phone_sprite(vid_img)
    slogan = text_layer([((W // 2, 1650), "Her kelime bir yıldız.", C.font(C.SERIF_I, 76), C.CREAM, "mm"),
                         ((W // 2, 1745), "Her yıldız bir kelime.", C.font(C.SERIF_I, 76), C.CREAM, "mm")])
    name = text_layer([((W // 2, 1855), C.AUTHOR, C.font(C.SERIF, 58), C.GOLD, "mm")])

    (s1a, s1b), (s2a, s2b), (s3a, s3b), (s4a, s4b), (s5a, s5b) = times
    s2s, s3s, s4s, s5s = s1b + GAP / 2, s2b + GAP / 2, s3b + GAP / 2, s4b + GAP / 2
    n = int(round(total * FPS))
    out = ROOT / "shorts" / f"00_giris_{variant}.mp4"
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    opening = Opening()
    switch = None
    for fi in range(n):
        t = fi / FPS
        vf = opening.frame()
        if vf is not None:
            fr = bg_frame(vf, t, total)
        else:
            if switch is None:
                switch = t
            fr = bg_frame(base, t, total)
            if opening.last is not None and t - switch < 0.6:   # son kareden sabit görsele yumuşak geçiş
                fr = Image.blend(bg_frame(opening.last, t, total), fr, ease((t - switch) / 0.6))
        # siyahtan açılış
        # başlık: sahne 1–2 ve 5'te
        ta = ease((t - 0.3) / 1.2) * (1 - ease((t - s3s) / 0.5)) + ease((t - s5s) / 0.8)
        if ta > 0.01:
            fr.alpha_composite(fade(title, min(ta, 1)))
            fr.alpha_composite(fade(subtitle, min(ta, 1) * ease((t - 1.0) / 1.0) if t < s3s else min(ta, 1)))
        # yıldızlar: sahne 2'de sırayla yanar, 3–4'te söner, 5'te hepsi geri gelir
        if s2s <= t:
            if t < s3s:
                prog = (t - s2s) / max(s2b - s2s, 0.1) * 30
            else:
                prog = 30
            k = min(30, int(prog))
            sa = (1 - ease((t - s3s) / 0.5)) + ease((t - s5s) / 0.8)
            sa = min(sa, 1)
            if sa > 0.01:
                lay = stars[k]
                if k < 30 and t < s3s:
                    lay = Image.blend(stars[k], stars[k + 1], prog - k)
                fr.alpha_composite(fade(lay, sa))
        # kartlar (sahne 3) ve telefon (sahne 4)
        if s3s - 0.2 <= t < s5s:
            da = ease((t - s3s) / 0.5) * (1 - ease((t - s5s + 0.6) / 0.6))
            fr.alpha_composite(fade(dim, da))
        if s3s <= t < s4s + 0.5:
            out_a = 1 - ease((t - s4s + 0.1) / 0.4)
            for k, (nn, ang, cx) in enumerate(sorted(cards, key=lambda c: c[1] == 0)):
                p = ease((t - s3s - 0.25 * k) / 0.8)
                sp = card_sp[nn]
                y = 1000 + (1 - p) * 1100
                fr.alpha_composite(fade(sp, out_a), (int(cx - sp.width / 2), int(y - sp.height / 2)))
        if s4s - 0.2 <= t < s5s:
            p_in = ease((t - s4s - 0.35) / 0.5)
            out_a = 1 - ease((t - s5s + 0.6) / 0.6)
            bx, by = (W - big.width) // 2, 230
            fr.alpha_composite(fade(big, p_in * out_a), (bx, by))
            # kartın QR'ı: big içinde (kart ölçeği 760/1748, gölge payı 40)
            sc = 760 / 1748
            qcx = bx + 40 + (1748 - 96 - 295 / 2) * sc
            qcy = by + 40 + (2480 - 96 - 295 / 2) * sc
            mv = ease((t - s4s - 0.7) / 0.9)
            px = qcx - 165
            py = qcy - 260 + (1 - mv) * 900
            dur4 = s5s - s4s
            scanned = t - s4s > 1.6 + 0.35 * dur4
            ph = phone_vid if scanned else phone_cam
            fr.alpha_composite(fade(ph, mv * out_a), (int(px), int(py)))
            if not scanned and mv > 0.95:      # tarama çizgisi
                d = ImageDraw.Draw(fr)
                sy = py + 60 + (math.sin((t - s4s) * 5) * 0.5 + 0.5) * 500
                d.line([px + 30, sy, px + 300, sy], fill=(90, 230, 140), width=6)
        # kapanış: slogan + isim
        if t > s5b + 0.3:
            ea = ease((t - s5b - 0.3) / 0.8)
            fr.alpha_composite(fade(slogan, ea))
            fr.alpha_composite(fade(name, ease((t - s5b - 0.9) / 0.8)))
        # altyazı
        for (txt, a, b), sl in zip(subs, sub_layers):
            if a <= t < b and t < s5b + 0.3:
                fr.alpha_composite(sl)
                break
        # siyahtan açılış / kapanışta karartma
        black = max(1 - ease(t / 0.8), ease((t - (total - 0.6)) / 0.6))
        if black > 0.01:
            fr.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * black))))
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close()
    enc.wait()
    (wd / "altyazi.json").write_text(json.dumps(subs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "ses-yz":
        ses_yz()
    elif cmd == "montaj":
        montaj(sys.argv[2])
    else:
        sys.exit(__doc__)
