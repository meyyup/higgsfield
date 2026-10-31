#!/usr/bin/env python3
"""Sözlüğün tamamı (A5, 40 sayfa): cover/sayfalar/PP.png + cards/Turkcenin_Yildizlari_sozluk_A5.pdf.

Sıra: kapak · proje yazısı · nasıl kullanılır · içindekiler · [bölüm sayfası + 10 kart] × 3 ·
senin yıldızın · künye · arka kapak. Önce scripts/cover.py ve scripts/cards.py --to 30 çalıştırılmış olmalı.
Künye bilgileri cover/kunye.txt'den (anahtar: değer), giriş videosu linki cover/giris_link.txt'den okunur.
"""
import csv
import pathlib
import sys

from PIL import Image, ImageDraw, ImageOps
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cover as C  # noqa: E402

ROOT = C.ROOT
W, H = C.W, C.H
PAPER = (255, 251, 243)
NAVY = (24, 34, 78)
INK = (45, 40, 50)
MUTED = (120, 112, 125)
GOLD_D = (190, 140, 50)                          # krem zemin üzerinde okunan altın
CARD_COL = {"Kültürümüz": (160, 82, 45), "Eski Sözcükler": (106, 63, 181), "Değerler": (196, 56, 94)}
SECTION_TXT = {
    "Kültürümüz": "Atalarımızdan bugüne taşıdığımız gelenekleri, yaşayışı ve birlikte olmanın sıcaklığını anlatan kelimeler.",
    "Eski Sözcükler": "Eski metinlerden, şiirlerden ve masallardan gelen; bugün az duyduğumuz ama hâlâ çok güzel olan kelimeler.",
    "Değerler": "Birbirimize nasıl davrandığımızı; iyiliği, dostluğu ve paylaşmayı anlatan kelimeler.",
}
PROJE = [
    "Gökyüzünde her yıldızın bir adı vardır; dilimizde de her kelimenin bir hikâyesi. Bu sözlükte, "
    "Türkçenin otuz güzel kelimesini üç takımyıldızda topladım: Kültürümüz, Eski Sözcükler ve Değerler.",
    "Her kartta kelimenin anlamını, bir örnek cümleyi ve küçük bir bilgiyi bulacaksınız. Kartın köşesindeki "
    "QR kodu okutursanız, kelime size kısa bir videoyla kendini anlatacak.",
    "Her kelime bir yıldız. Her yıldız bir kelime. Yeni bir kelime öğrenmek, gökyüzündeki yeni bir yıldızı "
    "tanımak gibidir. Yıldızları keşfedelim!",
]
X0 = C.BIND + 20                                  # metin sol kenarı (cilt payı + boşluk)
X1 = W - 130


def f_serif(s):
    return C.font(C.SERIF, s)


def f_serif_i(s):
    return C.font(C.SERIF_I, s)


def f_sans(s, w="Regular"):
    return C.font(C.F / f"NotoSans-{w}.ttf", s)


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


def paper_page():
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img)
    for x, y, r in [(1500, 230, 20), (1590, 330, 11), (1420, 380, 8), (300, 2280, 12), (1560, 2300, 9)]:
        C.star4(d, x, y, r, (232, 205, 150))
    return img


def page_no(img, n, dark=False):
    d = ImageDraw.Draw(img)
    d.text((W // 2 + C.BIND // 2, H - 70), str(n), font=f_serif(46), fill=C.CREAM if dark else MUTED, anchor="mm")


def heading(img, title, y=300, color=NAVY):
    d = ImageDraw.Draw(img)
    d.text((X0, y), title, font=f_serif(118), fill=color, anchor="ls")
    d.line([X0, y + 40, X0 + 220, y + 40], fill=GOLD_D, width=5)
    C.star4(d, X0 + 250, y + 40, 16, GOLD_D)


# ---------------------------------------------------------------- sayfalar
def p_proje():
    img = paper_page()
    heading(img, "Türkçenin Yıldızları")
    d = ImageDraw.Draw(img)
    f = f_serif(76)
    y = 520
    for i, para in enumerate(PROJE):
        if i == 0:                                # süslü ilk harf
            d.text((X0, y - 8), para[0], font=f_serif(230), fill=GOLD_D, anchor="lt")
            first = wrap(d, para[1:], f, X1 - X0 - 185)
            lines = first[:2]
            rest = " ".join(first[2:])
            for ln in lines:
                d.text((X0 + 175, y), ln, font=f, fill=INK, anchor="lt")
                y += 106
            for ln in wrap(d, rest, f, X1 - X0):
                d.text((X0, y), ln, font=f, fill=INK, anchor="lt")
                y += 106
        else:
            fi = f_serif_i(76) if i == 2 else f
            for ln in wrap(d, para, fi, X1 - X0):
                d.text((X0, y), ln, font=fi, fill=NAVY if i == 2 else INK, anchor="lt")
                y += 106
        y += 70
    # alt süs: üç renkli yıldız
    cx = W // 2 + C.BIND // 2
    for k, col in enumerate(CARD_COL.values()):
        d.polygon(star_pts(cx + (k - 1) * 110, H - 330, 34, 14), fill=col)
    page_no(img, 2)
    return img


def star_pts(cx, cy, r, ri):
    import math
    return [(cx + (r if i % 2 == 0 else ri) * math.cos(-math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else ri) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]


def icon_book(d, cx, cy, col):
    d.polygon([(cx - 150, cy - 70), (cx - 10, cy - 50), (cx - 10, cy + 90), (cx - 150, cy + 70)], outline=col, width=10)
    d.polygon([(cx + 150, cy - 70), (cx + 10, cy - 50), (cx + 10, cy + 90), (cx + 150, cy + 70)], outline=col, width=10)
    for k in range(3):
        d.line([cx - 125, cy - 30 + k * 35, cx - 35, cy - 18 + k * 35], fill=col, width=6)
        d.line([cx + 35, cy - 18 + k * 35, cx + 125, cy - 30 + k * 35], fill=col, width=6)


def icon_phone(d, cx, cy, col):
    d.rounded_rectangle([cx - 85, cy - 140, cx + 85, cy + 140], radius=28, outline=col, width=10)
    d.line([cx - 25, cy - 115, cx + 25, cy - 115], fill=col, width=8)
    s = 26
    for gx, gy in [(-1, -1), (1, -1), (-1, 1)]:
        x, y = cx + gx * 40, cy + gy * 40
        d.rectangle([x - s, y - s, x + s, y + s], outline=col, width=8)
        d.rectangle([x - 8, y - 8, x + 8, y + 8], fill=col)
    for x, y in [(cx + 22, cy + 22), (cx + 54, cy + 30), (cx + 30, cy + 58), (cx + 60, cy + 62)]:
        d.rectangle([x - 9, y - 9, x + 9, y + 9], fill=col)


def icon_play(d, cx, cy, col):
    d.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], outline=col, width=10)
    d.polygon([(cx - 35, cy - 60), (cx - 35, cy + 60), (cx + 65, cy)], fill=col)
    for k, r in enumerate((150, 185)):
        d.arc([cx - r, cy - r, cx + r, cy + r], -35, 35, fill=col, width=9)


def p_nasil():
    img = paper_page()
    heading(img, "Nasıl Kullanılır?")
    d = ImageDraw.Draw(img)
    steps = [
        ("Kelimeyi oku", "Kartta kelimenin anlamını, örnek cümleyi ve küçük bilgiyi oku.", icon_book),
        ("QR kodu okut", "Telefonunun kamerasını kartın köşesindeki QR koda tut.", icon_phone),
        ("İzle ve dinle", "Açılan kısa videoda kelimeyi dinle; görseliyle aklında tut.", icon_play),
    ]
    cols = list(CARD_COL.values())
    y = 600
    for i, (t, desc, icon) in enumerate(steps):
        col = cols[i]
        icon(d, X0 + 190, y + 110, col)
        tx = X0 + 450
        d.ellipse([tx, y - 10, tx + 90, y + 80], fill=col)
        d.text((tx + 45, y + 35), str(i + 1), font=f_sans(56, "Black"), fill="white", anchor="mm")
        d.text((tx + 120, y + 35), t, font=f_serif(84), fill=NAVY, anchor="lm")
        yy = y + 120
        for ln in wrap(d, desc, f_serif(56), X1 - tx):
            d.text((tx, yy), ln, font=f_serif(56), fill=INK, anchor="lt")
            yy += 72
        if i < 2:
            for k in range(5):
                d.ellipse([X0 + 182, y + 300 + k * 30, X0 + 198, y + 316 + k * 30], fill=(215, 200, 170))
        y += 520
    fn = f_serif_i(46)
    note = "QR kodların açılması için internet bağlantısı gerekir. Videoları bir büyüğünle birlikte izleyebilirsin."
    yy = H - 330
    for ln in wrap(d, note, fn, X1 - X0):
        d.text((X0, yy), ln, font=fn, fill=MUTED, anchor="lt")
        yy += 60
    page_no(img, 3)
    return img


def p_icindekiler(rows, start):
    img = paper_page()
    heading(img, "İçindekiler")
    d = ImageDraw.Draw(img)
    y = 470
    fw, fp = f_serif(54), f_serif(54)
    for cat, col in CARD_COL.items():
        y += 30
        d.polygon(star_pts(X0 + 26, y + 30, 26, 11), fill=col)
        C.spaced(d, (X0 + 75, y + 32), C_upper(cat), f_sans(40, "Bold"), col, 6, anchor="lm")
        d.text((X1, y + 32), str(start[cat]), font=f_serif(56), fill=col, anchor="rm")
        y += 95
        items = [r for r in rows if r["kategori"] == cat]
        colw = (X1 - X0 - 80) / 2
        for k, r in enumerate(items):
            cx = X0 + 40 + (k // 5) * (colw + 80)
            cy = y + (k % 5) * 70
            pg = str(start[cat] + k + 1)
            d.text((cx, cy), r["id"], font=f_sans(30, "Bold"), fill=col, anchor="lm")
            d.text((cx + 60, cy), r["kelime"], font=fw, fill=INK, anchor="lm")
            tw = d.textlength(r["kelime"], font=fw)
            pw = d.textlength(pg, font=fp)
            x = cx + 60 + tw + 18
            while x < cx + colw - pw - 18:      # nokta çizgisi
                d.ellipse([x, cy + 10, x + 5, cy + 15], fill=(200, 190, 175))
                x += 16
            d.text((cx + colw, cy), pg, font=fp, fill=MUTED, anchor="rm")
        y += 5 * 70 + 40
    ext = [("Senin Yıldızın", 38), ("Künye ve Kaynaklar", 39)]
    y += 10
    for t, pg in ext:
        d.text((X0, y), t, font=f_serif_i(58), fill=NAVY, anchor="lm")
        d.text((X1, y), str(pg), font=f_serif(56), fill=MUTED, anchor="rm")
        y += 80
    page_no(img, 4)
    return img


def C_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def night_bg(flip=False, darker=0):
    bg = C.background()
    if flip:
        bg = ImageOps.mirror(bg)
    if darker:
        bg.alpha_composite(Image.new("RGBA", bg.size, (5, 10, 35, darker)))
    return bg


def p_bolum(cat, words, no, page):
    img = night_bg(darker=60)
    d = ImageDraw.Draw(img)
    col = C.CATS[cat]
    d.text((W // 2, 300), f"{no}. Takımyıldız", font=f_serif_i(80), fill=C.GOLD, anchor="mm")
    C.spaced(d, (W // 2, 470), C_upper(cat), f_serif(150 if len(cat) < 12 else 128), C.CREAM, 10)
    d.line([W // 2 - 150, 570, W // 2 + 150, 570], fill=col, width=4)
    fdesc = f_serif_i(62)
    y = 640
    for ln in wrap(d, SECTION_TXT[cat], fdesc, W - 2 * C.BIND - 80):
        d.text((W // 2, y), ln, font=fdesc, fill=C.CREAM, anchor="ma")
        y += 80
    # takımyıldızı büyütüp ortala
    lay = C.LAYOUT[cat]
    xs = [p[0] for p in lay["pts"]]
    ys = [p[1] for p in lay["pts"]]
    sx = (W - 2 * 330) / (max(xs) - min(xs))
    sy = 520 / (max(ys) - min(ys))
    s = min(sx, sy)
    ox = W / 2 - s * (max(xs) + min(xs)) / 2
    oy = 1260 - s * (max(ys) + min(ys)) / 2
    big = {"pts": [(ox + s * x, oy + s * y, side) for x, y, side in lay["pts"]], "edges": lay["edges"],
           "label": (ox + s * lay["label"][0], oy + s * lay["label"][1])}
    saved = C.LAYOUT
    C.LAYOUT = {cat: big}
    saved_cats = C.CATS
    C.CATS = {cat: col}
    C.constellations(img, {cat: words})
    C.LAYOUT, C.CATS = saved, saved_cats
    page_no(img, page, dark=True)
    return img


def p_senin():
    img = paper_page()
    d = ImageDraw.Draw(img)
    band = 200
    d.rectangle([0, 0, W, band], fill=NAVY)
    d.text((96, band // 2), "SENİN YILDIZIN", font=f_sans(78, "Black"), fill="white", anchor="lm")
    fn = f_sans(70, "Bold")
    d.text((W - 96, band // 2), "31", font=fn, fill="white", anchor="rm")
    sx = W - 96 - d.textlength("31", font=fn) - 60
    d.polygon(star_pts(sx, band // 2 - 2, 38, 16), fill=(255, 205, 60))
    dash = (190, 175, 150)
    x0, y0, x1, y1 = 96, band + 60, W - 96, band + 60 + 900
    for x in range(x0, x1, 40):
        d.line([x, y0, x + 20, y0], fill=dash, width=5)
        d.line([x, y1, x + 20, y1], fill=dash, width=5)
    for y in range(y0, y1, 40):
        d.line([x0, y, x0, y + 20], fill=dash, width=5)
        d.line([x1, y, x1, y + 20], fill=dash, width=5)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 - 30), "Kelimenin resmini buraya çiz", font=f_serif_i(66), fill=dash, anchor="mm")
    d.polygon(star_pts((x0 + x1) / 2, (y0 + y1) / 2 + 70, 40, 16), outline=dash, width=4)
    y = y1 + 110
    d.text((96, y), "Kelimem:", font=f_serif(80), fill=NAVY, anchor="ls")
    d.line([420, y + 6, W - 96, y + 6], fill=dash, width=4)
    y += 100
    for label, n in (("ANLAMI", 2), ("ÖRNEK", 2), ("BİLİYOR MUSUN?", 2)):
        d.text((96, y), label, font=f_sans(40, "Bold"), fill=NAVY, anchor="ls")
        y += 30
        for _ in range(n):
            y += 80
            d.line([96, y, W - 96, y], fill=dash, width=3)
        y += 70
    f = f_serif_i(52)
    d.text((W // 2, H - 150), "Yaşayan bir sözlük büyümeye devam eder.", font=f, fill=MUTED, anchor="mm")
    page_no(img, 38)
    return img


def p_kunye():
    img = paper_page()
    heading(img, "Künye ve Kaynaklar")
    d = ImageDraw.Draw(img)
    info = {}
    kf = ROOT / "cover" / "kunye.txt"
    if kf.exists():
        for ln in kf.read_text(encoding="utf-8").splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1)
                info[k.strip()] = v.strip()
    y = 500
    fl, fv = f_sans(36, "Bold"), f_serif(60)
    for key in ("Hazırlayan", "Sınıf", "Okul", "Danışman Öğretmen"):
        d.text((X0, y), C_upper(key), font=fl, fill=GOLD_D, anchor="ls")
        y += 75
        if info.get(key):
            d.text((X0, y), info[key], font=fv, fill=INK, anchor="ls")
        else:
            d.line([X0, y + 5, X1, y + 5], fill=(200, 190, 175), width=3)
        y += 85
    y += 20
    blocks = [
        ("PROJE", "Dilimizin Zenginlikleri Projesi · Yaşayan Sözlük Tasarımı Yarışması, "
                  "İstanbul İl Millî Eğitim Müdürlüğü, 2026"),
        ("KAYNAK", "Kelime anlamları: Türk Dil Kurumu, Güncel Türkçe Sözlük (sozluk.gov.tr)"),
        ("YAPAY ZEKÂ KULLANIMI", "Kart ve kapak görselleri Higgsfield ile, video seslendirmeleri ElevenLabs ile "
                                 "yapay zekâ kullanılarak üretilmiştir."),
        ("VİDEOLAR", "Her kartın QR kodu, YouTube'da liste dışı yayımlanan kısa videosuna gider."),
        ("YAZI TİPLERİ", "Cormorant Garamond ve Noto Sans (SIL Open Font License)"),
    ]
    fb = f_serif(52)
    for key, val in blocks:
        d.text((X0, y), key, font=fl, fill=GOLD_D, anchor="ls")
        y += 70
        for ln in wrap(d, val, fb, X1 - X0):
            d.text((X0, y), ln, font=fb, fill=INK, anchor="ls")
            y += 66
        y += 40
    page_no(img, 39)
    return img


def p_arka():
    img = night_bg(flip=True, darker=40)
    d = ImageDraw.Draw(img)
    cx = W // 2
    d.text((cx, 520), "Her kelime bir yıldız.", font=f_serif_i(118), fill=C.CREAM, anchor="mm")
    d.text((cx, 670), "Her yıldız bir kelime.", font=f_serif_i(118), fill=C.CREAM, anchor="mm")
    C.star4(d, cx, 820, 26, C.GOLD)
    fs = f_serif(62)
    y = 930
    for ln in wrap(d, "Kültürümüz, Eski Sözcükler ve Değerler: Türkçenin otuz kelimesi, "
                      "otuz kart ve otuz kısa videoda.", fs, W - 2 * C.BIND - 60):
        d.text((cx, y), ln, font=fs, fill=C.CREAM, anchor="mm")
        y += 82
    C.spaced(d, (cx, y + 60), "TÜRKÇENİN YILDIZLARI", f_sans(38, "Bold"), C.GOLD, 8)
    C.spaced(d, (cx, y + 120), "DİLİMİZİN ZENGİNLİKLERİ PROJESİ", f_sans(30, "Bold"), C.CREAM, 6)
    C.qr_block(img)                                 # giriş videosu QR (kapakla aynı yer)
    return img


def card_page(nn, page):
    img = Image.open(ROOT / "cards" / "png" / f"{nn}.png").convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((W // 2, H - 42), str(page), font=f_serif(40), fill=MUTED, anchor="mm")
    return img


def main():
    rows = list(csv.DictReader((ROOT / "kelimeler.csv").open(encoding="utf-8")))
    words = {c: [r["kelime"] for r in rows if r["kategori"] == c] for c in C.CATS}
    start = {"Kültürümüz": 5, "Eski Sözcükler": 16, "Değerler": 27}
    pages = [Image.open(ROOT / "cover" / "kapak_A5.png").convert("RGBA"), p_proje(), p_nasil(),
             p_icindekiler(rows, start)]
    for no, cat in enumerate(C.CATS, 1):
        pages.append(p_bolum(cat, words[cat], no, start[cat]))
        for r in rows:
            if r["kategori"] == cat:
                pages.append(card_page(r["id"], len(pages) + 1))
    pages += [p_senin(), p_kunye(), p_arka()]
    assert len(pages) == 40, len(pages)
    outd = ROOT / "cover" / "sayfalar"
    outd.mkdir(parents=True, exist_ok=True)
    jd = ROOT / "work" / "book_jpg"
    jd.mkdir(parents=True, exist_ok=True)
    out = ROOT / "cards" / "Turkcenin_Yildizlari_sozluk_A5.pdf"
    c = canvas.Canvas(str(out), pagesize=(148 * mm, 210 * mm))
    c.setTitle("Türkçenin Yıldızları — Üç Takımyıldız, Otuz Kelime")
    px = 25.4 / C.DPI * mm
    card_ids = {start[cat] + k + 1: r["id"] for cat in start
                for k, r in enumerate([r for r in rows if r["kategori"] == cat])}
    links = {r["id"]: r["url"].strip() for r in csv.DictReader((ROOT / "links.csv").open(encoding="utf-8-sig"))}
    for i, img in enumerate(pages, 1):
        img = img.convert("RGB")
        img.save(outd / f"{i:02d}.png", dpi=(C.DPI, C.DPI))
        jpg = jd / f"{i:02d}.jpg"
        img.save(jpg, quality=92, dpi=(C.DPI, C.DPI))
        c.drawImage(str(jpg), 0, 0, 148 * mm, 210 * mm)
        nn = card_ids.get(i)
        qr = ROOT / "print" / "qr" / f"{nn}.png"
        if nn and links.get(nn) and qr.exists():   # kart QR'ı kayıpsız, tam yerine (25 mm)
            c.drawImage(str(qr), (W - 96 - C.QR_PX) * px, 96 * px, C.QR_PX * px, C.QR_PX * px)
        c.showPage()
    c.save()
    print(out.relative_to(ROOT), len(pages), "sayfa")


if __name__ == "__main__":
    main()
