#!/usr/bin/env python3
"""Basılı sözlük kartları (A5): cards/png/NN.png (300 dpi), cards/kartlar_A5_*.pdf (A5 sayfa, kart başına 1)
ve cards/kartlar_A4_kesim_*.pdf (A4 ortasında A5 + kesim işaretleri).

Kart A5, 148×210 mm. QR print/qr/NN.png'den 1:1 alınır (25×25 mm, sessiz alan dahil) — önce scripts/qr.py.
Yalnızca links.csv'de linki olan kartlar üretilir.

  python3 scripts/cards.py            # linki olan tüm kartlar
  python3 scripts/cards.py 01 02      # yalnızca bunlar
"""
import argparse
import csv
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_shorts import FONT, tr_upper  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DPI = 300
CW_MM, CH_MM = 148, 210
W, H = round(CW_MM / 25.4 * DPI), round(CH_MM / 25.4 * DPI)   # 1748 × 2480
M = 96                    # iç kenar boşluğu (~8 mm)
BAND = 200
IMG_H = 1080
BG = (255, 251, 243)
INK = (45, 40, 50)
QR_PX = 295               # 25 mm @ 300 dpi
CTA = "Oku, İzle ve Dinle"
# Görselin hangi yüksekliğinden kırpılacağı (0 = üst, 1 = alt); varsayılan orta.
FOCUS = {"01": 0.47, "02": 0.45, "03": 0.45, "05": 0.42, "06": 0.75, "07": 0.72,
         "11": 0.6, "14": 0.66, "17": 0.38, "19": 0.42, "20": 0.62,
         "21": 0.51, "24": 0.46, "25": 0.54, "27": 0.55, "29": 0.5}
# Dikey kompozisyonu kırpılınca bozulanlar: tam görsel ortada, kenarlar bulanık uzantıyla dolu.
FIT = {"04", "08", "09", "10", "12", "13", "15", "16", "18", "22", "23", "26", "28", "30"}


def font(w, size):
    return ImageFont.truetype(FONT[w], size)


def star(cx, cy, r, ri):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else ri
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


def fit_blur(img, w, h):
    bg = cover(img, w, h, 0.5).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", bg.size, BG), 0.15)
    s = h / img.height
    fg = img.resize((round(img.width * s), h), Image.LANCZOS)
    fade = 90                                   # kenarları bulanık zemine yumuşakça karıştır
    mask = Image.new("L", fg.size, 255)
    md = ImageDraw.Draw(mask)
    for i in range(fade):
        v = int(255 * i / fade)
        md.line([(i, 0), (i, h)], fill=v)
        md.line([(fg.width - 1 - i, 0), (fg.width - 1 - i, h)], fill=v)
    bg.paste(fg, ((w - fg.width) // 2, 0), mask)
    return bg


def cover(img, w, h, focus):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    top = int((img.height - h) * focus)
    left = (img.width - w) // 2
    return img.crop((left, top, left + w, top + h))


def blocks(row):
    return [("ANLAMI", row["anlami"]), ("ÖRNEK", f"“{row['ornek_cumle']}”"),
            ("BİLİYOR MUSUN?", row["bilgi"])]


def card(row, out):
    nn, color = row["id"], hex2rgb(row["renk"])
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # üst bant
    d.rectangle([0, 0, W, BAND], fill=color)
    d.text((M, BAND // 2), tr_upper(row["kategori"]), font=font("Black", 78), fill="white", anchor="lm")
    fn = font("Bold", 70)
    num = f"{nn}/30"
    d.text((W - M, BAND // 2), num, font=fn, fill="white", anchor="rm")
    sx = W - M - d.textlength(num, font=fn) - 22 - 38          # yıldız: sayının solunda
    d.polygon(star(sx, BAND // 2 - 2, 38, 16), fill=(255, 205, 60))

    # görsel
    src = Image.open(ROOT / "images" / f"{nn}.png").convert("RGB")
    pic = fit_blur(src, W, IMG_H) if nn in FIT else cover(src, W, IMG_H, FOCUS.get(nn, 0.5))
    img.paste(pic, (0, BAND))
    d.rectangle([0, BAND + IMG_H, W, BAND + IMG_H + 14], fill=color)

    # kelime
    y = BAND + IMG_H + 14 + 60
    fw = font("Black", 170)
    while d.textlength(row["kelime"], font=fw) > W - 2 * M:
        fw = font("Black", fw.size - 4)
    d.text((M, y), row["kelime"], font=fw, fill=color, anchor="lt")
    y += fw.size + 50

    # metin blokları: alt bölgeye (QR) kadar sığacak en büyük punto
    bottom_zone = H - M - QR_PX - 50
    maxw = W - 2 * M
    for size in range(66, 34, -1):
        fb, fl = font("Regular", size), font("Bold", int(size * 0.72))
        plan, yy = [], y
        for label, text in blocks(row):
            lines = wrap(d, text, fb, maxw)
            plan.append((label, lines, yy))
            yy += int(fl.size * 1.35) + len(lines) * int(size * 1.32) + int(size * 0.6)
        if yy <= bottom_zone:
            break
    for label, lines, yy in plan:
        d.text((M, yy), label, font=fl, fill=color, anchor="lt")
        yy += int(fl.size * 1.35)
        for ln in lines:
            d.text((M, yy), ln, font=fb, fill=INK, anchor="lt")
            yy += int(size * 1.32)

    # alt bölge: QR + çağrı + künye
    qr_path = ROOT / "print" / "qr" / f"{nn}.png"
    if has_qr(nn):
        qr = Image.open(qr_path).convert("RGB")
        assert qr.size == (QR_PX, QR_PX), qr.size
    else:                                   # link henüz yok: yer tutucu kutu
        qr = Image.new("RGB", (QR_PX, QR_PX), "white")
        qd = ImageDraw.Draw(qr)
        for i in range(0, QR_PX, 24):       # kesik çerçeve
            for seg in ([i, 0, i + 12, 0], [i, QR_PX - 1, i + 12, QR_PX - 1],
                        [0, i, 0, i + 12], [QR_PX - 1, i, QR_PX - 1, i + 12]):
                qd.line(seg, fill=(150, 150, 150), width=4)
        qd.text((QR_PX // 2, QR_PX // 2 - 26), "QR", font=font("Black", 64), fill=(150, 150, 150), anchor="mm")
        qd.text((QR_PX // 2, QR_PX // 2 + 40), "yakında", font=font("Bold", 40), fill=(150, 150, 150), anchor="mm")
    qx, qy = W - M - QR_PX, H - M - QR_PX
    img.paste(qr, (qx, qy))
    tx = M
    tw = qx - M - 30
    d.line([tx, qy - 20, qx - 40, qy - 20], fill=color, width=5)
    fc = font("Black", 92)
    cy = qy + QR_PX // 2                    # QR'ın dikey ortası
    d.text((tx, cy), CTA, font=fc, fill=INK, anchor="lm")
    ax = qx - 40                            # ok: çizgi + üçgen (fontta → glifi yok)
    ex = tx + d.textlength(CTA, font=fc) + 44
    d.line([ex, cy, ax - 34, cy], fill=color, width=14)
    d.polygon([(ax, cy), (ax - 48, cy - 32), (ax - 48, cy + 32)], fill=color)
    img.save(out, dpi=(DPI, DPI))


LINKS = {}


def has_qr(nn):
    return bool(LINKS.get(nn)) and (ROOT / "print" / "qr" / f"{nn}.png").exists()


def place(c, path, x, y):
    """Kart: görsel JPEG (küçük dosya) + QR kayıpsız PNG, tam yerine (25 mm)."""
    jpg = ROOT / "work" / "cards_jpg" / f"{path.stem}.jpg"
    jpg.parent.mkdir(parents=True, exist_ok=True)
    Image.open(path).convert("RGB").save(jpg, quality=92, dpi=(DPI, DPI))
    c.drawImage(str(jpg), x, y, CW_MM * mm, CH_MM * mm)
    px = 25.4 / DPI * mm
    if has_qr(path.stem):
        c.drawImage(str(ROOT / "print" / "qr" / f"{path.stem}.png"),
                    x + (W - M - QR_PX) * px, y + M * px, QR_PX * px, QR_PX * px)


def pdf(paths, out_a5, out_a4):
    pdfmetrics.registerFont(TTFont("NotoB", str(ROOT / "fonts" / "NotoSans-Bold.ttf")))
    cw, ch = CW_MM * mm, CH_MM * mm
    c = canvas.Canvas(str(out_a5), pagesize=(cw, ch))
    c.setTitle("Kelime Takımyıldızı — sözlük kartları (A5)")
    for p in paths:
        place(c, p, 0, 0)
        c.showPage()
    c.save()
    PW, PH = A4
    x, y = (PW - cw) / 2, (PH - ch) / 2
    c = canvas.Canvas(str(out_a4), pagesize=A4)
    c.setTitle("Kelime Takımyıldızı — sözlük kartları (A4 üzerine A5, kesim işaretli)")
    for p in paths:
        c.setFont("NotoB", 9)
        c.drawCentredString(PW / 2, PH - 12 * mm, "%100 ölçekte basın, sayfaya sığdırmayın — kart A5 (148 × 210 mm), QR 25 × 25 mm")
        place(c, p, x, y)
        c.setLineWidth(0.3)
        c.setStrokeGray(0.3)
        L, o = 6 * mm, 2 * mm
        for cx, cy, sx, sy in [(x, y, -1, -1), (x + cw, y, 1, -1), (x, y + ch, -1, 1), (x + cw, y + ch, 1, 1)]:
            c.line(cx + sx * o, cy, cx + sx * (o + L), cy)
            c.line(cx, cy + sy * o, cx, cy + sy * (o + L))
        c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--to", help="bu id'ye kadar tüm kartlar; linki olmayanlarda 'QR yakında' kutusu")
    a = ap.parse_args()
    LINKS.update({r["id"]: r["url"].strip()
                  for r in csv.DictReader((ROOT / "links.csv").open(encoding="utf-8-sig"))})
    rows = [r for r in csv.DictReader((ROOT / "kelimeler.csv").open(encoding="utf-8"))
            if (r["id"] <= a.to if a.to else LINKS.get(r["id"])) and (not a.ids or r["id"] in a.ids)]
    missing = [r["id"] for r in rows if not has_qr(r["id"])]
    if missing:
        print("QR yok (yer tutucu):", " ".join(missing))
    outd = ROOT / "cards" / "png"
    outd.mkdir(parents=True, exist_ok=True)
    paths = []
    for r in rows:
        p = outd / f"{r['id']}.png"
        card(r, p)
        paths.append(p)
        print(p.relative_to(ROOT))
    if paths:
        rng = f"{rows[0]['id']}-{rows[-1]['id']}"
        pdf(paths, ROOT / "cards" / f"kartlar_A5_{rng}.pdf", ROOT / "cards" / f"kartlar_A4_kesim_{rng}.pdf")
        print(f"cards/kartlar_A5_{rng}.pdf, cards/kartlar_A4_kesim_{rng}.pdf")


if __name__ == "__main__":
    main()
