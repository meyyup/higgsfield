#!/usr/bin/env python3
"""Defter ön kapağı (A5, 300 dpi): cover/kapak_A5.png + cover/kapak_A5.pdf.

Arka plan: cover/kapak_arka_D.png (Higgsfield). Üstte başlık, ortada 30 kelimelik üç takımyıldız,
altta illüstrasyon ve giriş videosu QR'ı (cover/giris_link.txt varsa gerçek QR, yoksa yer tutucu).
"""
import csv
import math
import pathlib
import random

import qrcode
from qrcode.constants import ERROR_CORRECT_Q
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = pathlib.Path(__file__).resolve().parent.parent
DPI = 300
W, H = 1748, 2480                       # A5
BIND = 170                              # sol kenar: delgeç / cilt payı
CREAM = (246, 234, 204)
GOLD = (233, 196, 120)
F = ROOT / "fonts"
SERIF = F / "CormorantGaramond-SemiBold.ttf"
SERIF_I = F / "CormorantGaramond-SemiBoldItalic.ttf"
SANS_B = F / "NotoSans-Bold.ttf"
QR_PX = 295                             # 25 mm

# Kart renklerinin koyu zemin üzerinde okunacak açık tonları
CATS = {
    "Kültürümüz": (242, 166, 98),
    "Eski Sözcükler": (184, 160, 246),
    "Değerler": (244, 140, 178),
}
# Takımyıldız yerleşimi: kategori başına 10 yıldız (kelimeler.csv sırasıyla) — (x, y, etiket yönü)
# yön: b = üstte, t = altta, l = sağda, r = solda
LAYOUT = {
    "Kültürümüz": dict(pts=[(260, 840, "b"), (470, 800, "b"), (680, 870, "l"), (720, 1050, "l"), (600, 1200, "l"),
                            (390, 1210, "t"), (240, 1090, "t"), (220, 950, "l"), (430, 950, "b"), (560, 1010, "t")],
                       edges=[(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0), (1, 8), (8, 9), (9, 3)],
                       label=(470, 1130)),
    "Eski Sözcükler": dict(pts=[(1090, 840, "b"), (1300, 800, "b"), (1510, 860, "b"), (1610, 1010, "r"),
                                (1520, 1170, "t"), (1310, 1210, "t"), (1100, 1160, "t"), (1020, 1010, "l"),
                                (1210, 960, "b"), (1400, 1035, "b")],
                           edges=[(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 0), (7, 8), (8, 9), (9, 3)],
                           label=(1300, 1115)),
    "Değerler": dict(pts=[(480, 1400, "b"), (680, 1360, "b"), (900, 1390, "b"), (1120, 1350, "b"), (1340, 1400, "b"),
                          (1430, 1500, "t"), (1180, 1570, "t"), (980, 1505, "t"), (730, 1545, "t"), (500, 1560, "t")],
                     edges=[(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 0)],
                     label=(930, 1455)),
}


def font(path, size):
    return ImageFont.truetype(str(path), size)


def spaced(d, xy, text, f, fill, spacing, anchor="mm"):
    """Harf aralıklı yazı (ortalı)."""
    widths = [d.textlength(c, font=f) for c in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = xy[0] - total / 2 if anchor == "mm" else xy[0]
    for c, w in zip(text, widths):
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="lm")
        x += w + spacing


def star4(d, cx, cy, r, fill):
    """Dört köşeli parıltı."""
    k = r * 0.28
    d.polygon([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
               (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], fill=fill)


def glow(img, cx, cy, r, color, alpha=150):
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (alpha,))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.6)))


def background():
    src = Image.open(ROOT / "cover" / "kapak_arka_D.png").convert("RGB")
    ill = src.resize((W, round(src.height * W / src.width)), Image.LANCZOS)
    bg = Image.new("RGB", (W, H))
    bg.paste(ill, (0, H - ill.height))               # alttan hizalı; üstteki fazla gök kırpılır
    bg = bg.convert("RGBA")
    # başlık okunurluğu için üstte hafif koyulaştırma
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(800):
        sd.line([(0, y), (W, y)], fill=(5, 10, 35, int(90 * (1 - y / 800))))
    bg.alpha_composite(shade)
    return bg


def constellations(img, words):
    d = ImageDraw.Draw(img)
    fw = font(SERIF_I, 52)
    fl = font(SANS_B, 26)
    for cat, color in CATS.items():
        lay = LAYOUT[cat]
        pts = lay["pts"]
        line = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(line)
        for a, b in lay["edges"]:
            ld.line([pts[a][:2], pts[b][:2]], fill=color + (150,), width=3)
        img.alpha_composite(line)
        for i, (x, y, _) in enumerate(pts):
            big = i == 0
            glow(img, x, y, 34 if big else 20, color, 120 if big else 90)
            r = 13 if big else 8
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)
            d.ellipse([x - r / 2.5, y - r / 2.5, x + r / 2.5, y + r / 2.5], fill=(255, 250, 235))
        for (x, y, side), w in zip(pts, words[cat]):
            off = 24
            tx, ty, anchor = {"b": (x, y - off, "md"), "t": (x, y + off, "ma"),
                              "l": (x + off, y, "lm"), "r": (x - off, y, "rm")}[side]
            d.text((tx + 2, ty + 3), w, font=fw, fill=(0, 0, 20), anchor=anchor)
            d.text((tx, ty), w, font=fw, fill=color, anchor=anchor)
        spaced(d, lay["label"], cat.replace("i", "İ").upper(), fl, color, 7)


def titles(img):
    d = ImageDraw.Draw(img)
    cx = W // 2
    ft = font(SERIF, 184)
    spaced(d, (cx, 190), "TÜRKÇENİN", ft, CREAM, 14)
    spaced(d, (cx, 415), "YILDIZLARI", ft, CREAM, 14)
    fs = font(SERIF_I, 84)
    sub = "Üç Takımyıldız, Otuz Kelime"
    d.text((cx, 550), sub, font=fs, fill=GOLD, anchor="mm")
    sw = d.textlength(sub, font=fs) / 2
    star4(d, cx - sw - 60, 555, 22, GOLD)
    star4(d, cx + sw + 60, 555, 22, GOLD)
    d.line([cx - 150, 622, cx + 150, 622], fill=GOLD, width=3)
    spaced(d, (cx, 668), "DİLİMİZİN ZENGİNLİKLERİ PROJESİ", font(SANS_B, 32), CREAM, 7)


def bottom(img):
    d = ImageDraw.Draw(img)
    # proje adı: altta, çimen üzerinde okunacak koyu şerit
    band = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for y in range(H - 500, H):
        bd.line([(0, y), (W, y)], fill=(5, 12, 30, int(120 * (y - (H - 500)) / 500)))
    img.alpha_composite(band)
    fsl = font(SERIF_I, 72)
    d.text((BIND, H - 300), "Her yıldız bir kelime.", font=fsl, fill=CREAM, anchor="lm")
    d.text((BIND, H - 205), "Her kelime bir yıldız.", font=fsl, fill=CREAM, anchor="lm")
    qr_block(img)


def qr_block(img):
    """Giriş videosu QR'ı (sağ alt): cover/giris_link.txt varsa gerçek QR, yoksa yer tutucu."""
    d = ImageDraw.Draw(img)
    qx, qy = W - 120 - QR_PX, H - 170 - QR_PX
    link_file = ROOT / "cover" / "giris_link.txt"
    if link_file.exists() and link_file.read_text().strip():
        q = qrcode.QRCode(error_correction=ERROR_CORRECT_Q, border=4, box_size=1)
        q.add_data(link_file.read_text().strip())
        q.make(fit=True)
        img.paste(q.make_image(fill_color="black", back_color="white").convert("RGB")
                  .resize((QR_PX, QR_PX), Image.NEAREST), (qx, qy))
    else:
        for i in range(0, QR_PX, 26):
            for seg in ([qx + i, qy, qx + i + 13, qy], [qx + i, qy + QR_PX, qx + i + 13, qy + QR_PX],
                        [qx, qy + i, qx, qy + i + 13], [qx + QR_PX, qy + i, qx + QR_PX, qy + i + 13]):
                d.line(seg, fill=GOLD, width=4)
        d.text((qx + QR_PX / 2, qy + QR_PX / 2), "QR", font=font(SANS_B, 60), fill=GOLD, anchor="mm")
    spaced(d, (qx + QR_PX / 2, qy + QR_PX + 45), "GİRİŞ VİDEOSU", font(SANS_B, 28), CREAM, 5)


def main():
    rows = list(csv.DictReader((ROOT / "kelimeler.csv").open(encoding="utf-8")))
    words = {c: [r["kelime"] for r in rows if r["kategori"] == c] for c in CATS}
    img = background()
    titles(img)
    constellations(img, words)
    bottom(img)
    out = ROOT / "cover" / "kapak_A5.png"
    img.convert("RGB").save(out, dpi=(DPI, DPI))
    jpg = ROOT / "work" / "kapak.jpg"
    img.convert("RGB").save(jpg, quality=93, dpi=(DPI, DPI))
    c = canvas.Canvas(str(ROOT / "cover" / "kapak_A5.pdf"), pagesize=(148 * mm, 210 * mm))
    c.setTitle("Türkçenin Yıldızları — ön kapak")
    c.drawImage(str(jpg), 0, 0, 148 * mm, 210 * mm)
    c.save()
    print("cover/kapak_A5.png, cover/kapak_A5.pdf")


if __name__ == "__main__":
    main()
