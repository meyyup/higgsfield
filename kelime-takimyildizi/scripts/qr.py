#!/usr/bin/env python3
"""G5 — links.csv → print/qr_etiketleri.pdf (+ print/qr/NN.png, print/qr_dogrulama.md).

QR: statik, hata düzeltme Q, 4 modül sessiz alan, sessiz alan dahil 25×25 mm, 300 dpi.
PDF: A4, 5×6 kesim işaretli ızgara, kenarda "%100 ölçekte basın, sayfaya sığdırmayın".
Doğrulama: her PNG ve PDF'in 300 dpi raster hali OpenCV ile geri okunur, URL ile birebir karşılaştırılır.

  python3 scripts/qr.py                    # links.csv
  python3 scripts/qr.py --links work/ornek_links.csv --out work/qr_test   # deneme
"""
import argparse
import csv
import pathlib
import re
import subprocess
import sys

import cv2
import qrcode
from qrcode.constants import ERROR_CORRECT_Q
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = pathlib.Path(__file__).resolve().parent.parent
QR_MM, DPI = 25.0, 300
COLS, ROWS = 5, 6
CELL_W, CELL_H = 36 * mm, 40 * mm
VID = r"[A-Za-z0-9_-]{11}"
PATTERNS = [
    re.compile(rf"^https://(www\.|m\.)?youtube\.com/shorts/{VID}([?&][^\s]*)?$"),
    re.compile(rf"^https://youtu\.be/{VID}([?&][^\s]*)?$"),
    re.compile(rf"^https://(www\.|m\.)?youtube\.com/watch\?v={VID}(&[^\s]*)?$"),
]


def load(links_path):
    words = {r["id"]: r["kelime"] for r in csv.DictReader((ROOT / "kelimeler.csv").open(encoding="utf-8"))}
    got = {}
    problems = []
    with links_path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            nn = (r.get("id") or "").strip().zfill(2)
            url = (r.get("url") or "").strip()
            if nn not in words:
                problems.append(f"bilinmeyen id: {r.get('id')!r}")
            elif not url:
                problems.append(f"{nn} {words[nn]}: URL boş")
            elif not any(p.match(url) for p in PATTERNS):
                problems.append(f"{nn} {words[nn]}: URL biçimi hatalı: {url}")
            elif nn in got:
                problems.append(f"{nn} {words[nn]}: iki kez yazılmış")
            else:
                got[nn] = url
    for nn in words:
        if nn not in got and not any(p.startswith(nn + " ") for p in problems):
            problems.append(f"{nn} {words[nn]}: satır yok")
    dup = {u for u in got.values() if list(got.values()).count(u) > 1}
    for nn, u in got.items():
        if u in dup:
            problems.append(f"{nn} {words[nn]}: aynı URL başka satırda da var")
    return words, got, problems


def make_png(url, path):
    q = qrcode.QRCode(error_correction=ERROR_CORRECT_Q, border=4, box_size=1)
    q.add_data(url)
    q.make(fit=True)
    modules = q.modules_count + 8
    px = round(QR_MM / 25.4 * DPI)                      # 295 px
    img = q.make_image(fill_color="black", back_color="white").convert("L")
    img = img.resize((px, px), resample=0)             # en yakın komşu: keskin modüller
    img.save(path, dpi=(DPI, DPI))
    return q.version, modules, QR_MM / modules


def decode(img):
    det = cv2.QRCodeDetector()
    ok, texts, _, _ = det.detectAndDecodeMulti(img)
    return [t for t in texts if t] if ok else []


def pdf(words, got, pngs, out):
    pdfmetrics.registerFont(TTFont("Noto", str(ROOT / "fonts" / "NotoSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("NotoB", str(ROOT / "fonts" / "NotoSans-Bold.ttf")))
    W, H = A4
    x0 = (W - COLS * CELL_W) / 2
    y_top = (H + ROWS * CELL_H) / 2
    c = canvas.Canvas(str(out), pagesize=A4)
    c.setTitle("Kelime Takımyıldızı — QR etiketleri")
    ids = sorted(got)
    per = COLS * ROWS
    for p in range(0, len(ids), per):
        c.setFont("NotoB", 10)
        c.drawCentredString(W / 2, H - 10 * mm, "%100 ölçekte basın, sayfaya sığdırmayın")
        c.setFont("Noto", 7)
        c.drawCentredString(W / 2, H - 14 * mm, "Yazdırma: Gerçek boyut / Ölçek %100 — her QR 25 × 25 mm")
        c.saveState()
        c.translate(7 * mm, H / 2)
        c.rotate(90)
        c.setFont("NotoB", 9)
        c.drawCentredString(0, 0, "%100 ölçekte basın, sayfaya sığdırmayın")
        c.restoreState()
        c.drawCentredString(W / 2, 8 * mm, "Kelime Takımyıldızı · Türkçenin Kelime Hazinesi")
        # 25 mm kontrol çizgisi
        c.setLineWidth(0.4)
        c.line(x0, 16 * mm, x0 + 25 * mm, 16 * mm)
        c.line(x0, 15 * mm, x0, 17 * mm)
        c.line(x0 + 25 * mm, 15 * mm, x0 + 25 * mm, 17 * mm)
        c.setFont("Noto", 6.5)
        c.drawString(x0 + 27 * mm, 15.2 * mm, "← bu çizgi basılı kâğıtta 25 mm olmalı")
        for k, nn in enumerate(ids[p:p + per]):
            col, row = k % COLS, k // COLS
            cx = x0 + col * CELL_W
            cy = y_top - (row + 1) * CELL_H
            qx = cx + (CELL_W - QR_MM * mm) / 2
            qy = cy + CELL_H - 4 * mm - QR_MM * mm
            c.drawImage(str(pngs[nn]), qx, qy, QR_MM * mm, QR_MM * mm)
            c.setFont("NotoB", 8)
            c.drawCentredString(cx + CELL_W / 2, qy - 4.5 * mm, f"{nn} · {words[nn]}")
        # kesim işaretleri: ızgara kesişimlerinde küçük artı
        c.setLineWidth(0.3)
        c.setStrokeGray(0.35)
        m = 2 * mm
        for i in range(COLS + 1):
            for j in range(ROWS + 1):
                X, Y = x0 + i * CELL_W, y_top - j * CELL_H
                c.line(X - m, Y, X + m, Y)
                c.line(X, Y - m, X, Y + m)
        c.setStrokeGray(0)
        c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--links", default="links.csv")
    ap.add_argument("--out", default="print")
    a = ap.parse_args()
    out = ROOT / a.out
    (out / "qr").mkdir(parents=True, exist_ok=True)
    words, got, problems = load(ROOT / a.links)
    rep = ["# QR doğrulama raporu", ""]
    if problems:
        rep += ["## links.csv sorunları", ""] + [f"- {p}" for p in problems] + [""]
    rep += ["| id | kelime | URL | sürüm | modül boyu (mm) | PNG okuma | PDF okuma |", "|---|---|---|---|---|---|---|"]
    pngs, results = {}, {}
    for nn in sorted(got):
        pngs[nn] = out / "qr" / f"{nn}.png"
        ver, mods, msz = make_png(got[nn], pngs[nn])
        dec = decode(cv2.imread(str(pngs[nn])))
        results[nn] = [ver, msz, dec == [got[nn]], None]
    pdf_path = out / "qr_etiketleri.pdf"
    if got:
        pdf(words, got, pngs, pdf_path)
        # PDF'i 300 dpi'de rasterleştir, her hücreyi kesip ayrı oku
        ras = out / "_pdf_raster"
        subprocess.run(["pdftoppm", "-r", str(DPI), "-png", str(pdf_path), str(ras)], check=True)
        pages = sorted(out.glob("_pdf_raster*.png"))
        W, H = A4
        x0 = (W - COLS * CELL_W) / 2
        y_top = (H + ROWS * CELL_H) / 2
        s = DPI / 72
        ids = sorted(got)
        for k, nn in enumerate(ids):
            pg = cv2.imread(str(pages[k // (COLS * ROWS)]))
            kk = k % (COLS * ROWS)
            col, row = kk % COLS, kk // COLS
            left = int((x0 + col * CELL_W) * s)
            top = int((H - y_top + row * CELL_H) * s)
            crop = pg[top:top + int(CELL_H * s), left:left + int(CELL_W * s)]
            results[nn][3] = decode(crop) == [got[nn]]
        for pth in pages:
            pth.unlink()
    for nn in sorted(got):
        ver, msz, okp, okd = results[nn]
        rep.append(f"| {nn} | {words[nn]} | {got[nn]} | {ver} | {msz:.2f} | {'✓' if okp else '✗'} | {'✓' if okd else '✗'} |")
    good = sum(1 for r in results.values() if r[2] and r[3])
    rep += ["", f"Sonuç: {good}/30 QR geri okumada birebir doğru URL'yi verdi."
            + ("" if not problems else f" links.csv'de {len(problems)} sorun var (yukarıda).")]
    (out / "qr_dogrulama.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep[:2 + (len(problems) + 3 if problems else 0)]))
    print(rep[-1])
    sys.exit(0 if good == 30 and not problems else 1)


if __name__ == "__main__":
    main()
