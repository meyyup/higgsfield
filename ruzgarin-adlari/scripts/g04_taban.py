"""G4 — print/taban_ruzgar_gulu.pdf: 60×50 cm tabanın 1:1 çizimi, A4 sayfalara bölünmüş.

Kullanım: python3 scripts/g04_taban.py [--pusula 5]   (pusula yuvası çapı, cm)
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from common import (A4P, F, FB, PRINT, PROJE_ADI, ALT_BASLIK, TABAN, YONLER,  # noqa: E402
                    boyut_yazi, fmt, maddeleri_oku, sayfa_cercevesi)
from yerlesim import TABAN_MERKEZ, kutular_denetle, taban_yerlesimi  # noqa: E402

# Sayfa içerik alanı (A4 dikey) ve bindirme payı
KS, KU = 0.8, 1.2           # sol ve üst kenar
ALAN_W, ALAN_H = 19.4, 27.2
BINDIRME = 1.0


class Donusum:
    """Taban koordinatı (cm) -> sayfa noktası."""

    def __init__(self, ox, oy, px, py_ust, olcek=1.0):
        self.ox, self.oy, self.px, self.py, self.s = ox, oy, px, py_ust, olcek

    def X(self, x):
        return (self.px + (x - self.ox) * self.s) * cm

    def Y(self, y):
        return (self.py - (y - self.oy) * self.s) * cm

    def L(self, d):
        return d * self.s * cm


def taban_ciz(c, T, yer, pusula, izgara=True):
    s = T.s
    W, H = TABAN
    # Taban dış kenarı
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1.2)
    c.rect(T.X(0), T.Y(H), T.L(W), T.L(H))
    # Kenar adları
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.setFont(F, max(5, 9 * s))
    c.drawCentredString(T.X(W / 2), T.Y(0) + 0.15 * cm, "ARKA DUVAR TARAFI")
    c.drawCentredString(T.X(W / 2), T.Y(H) - 0.45 * cm * max(s, 0.6), "ÖN (AÇIK) TARAF")

    # Hizalama ızgarası: her 10 cm'de + işareti ve koordinat
    if izgara:
        c.setStrokeColorRGB(0.6, 0.6, 0.6)
        c.setLineWidth(0.4)
        c.setFont(F, 5)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        for gx in range(0, int(W) + 1, 5):
            for gy in range(0, int(H) + 1, 5):
                u = 0.5 if (gx % 10 == 0 and gy % 10 == 0) else 0.25
                c.line(T.X(gx - u), T.Y(gy), T.X(gx + u), T.Y(gy))
                c.line(T.X(gx), T.Y(gy - u), T.X(gx), T.Y(gy + u))
                if gx % 10 == 0 and gy % 10 == 0:
                    c.drawString(T.X(gx + 0.12), T.Y(gy - 0.12), f"{gx},{gy}")

    mx, my = TABAN_MERKEZ
    # Elle çizilecek rüzgâr gülü için açık gri yıldız (8 kollu)
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.setLineWidth(0.6)
    yol = c.beginPath()
    for i in range(16):
        a = math.radians(-90 + i * 22.5)
        if i % 4 == 0:
            r = 9.0          # ana yönler
        elif i % 2 == 0:
            r = 6.0          # ara yönler
        else:
            r = 1.8 + pusula / 2
        px, py = mx + r * math.cos(a), my + r * math.sin(a)
        (yol.moveTo if i == 0 else yol.lineTo)(T.X(px), T.Y(py))
    yol.close()
    c.drawPath(yol, stroke=1, fill=0)

    # Yön çizgileri: pusula yuvasından kart kenarına
    kartlar = {e: (x, y, w, h) for r, x, y, w, h, e in yer}
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.9)
    for kod in YONLER:
        x, y, w, h = kartlar[kod]
        cx, cy = x + w / 2, y + h / 2
        dx, dy = cx - mx, cy - my
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        # kart dikdörtgenine giriş noktası
        tx = (w / 2) / abs(ux) if ux else 1e9
        ty = (h / 2) / abs(uy) if uy else 1e9
        bitis = d - min(tx, ty) - 0.4
        bas = pusula / 2 + 0.3
        c.line(T.X(mx + ux * bas), T.Y(my + uy * bas), T.X(mx + ux * bitis), T.Y(my + uy * bitis))
        lx, ly = mx + ux * (bitis - 1.6), my + uy * (bitis - 1.6)
        c.setFont(FB, max(6, 22 * s))
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(T.X(lx + uy * 0.9), T.Y(ly - ux * 0.9) - 7 * s, kod)

    # Pusula yuvası
    c.setLineWidth(1.0)
    c.setDash(3, 2)
    c.circle(T.X(mx), T.Y(my), T.L(pusula / 2))
    c.setDash()
    c.setLineWidth(0.4)
    c.line(T.X(mx - 0.4), T.Y(my), T.X(mx + 0.4), T.Y(my))
    c.line(T.X(mx), T.Y(my - 0.4), T.X(mx), T.Y(my + 0.4))
    c.setFont(F, max(4.5, 7 * s))
    c.drawCentredString(T.X(mx), T.Y(my + pusula / 2 + 0.5), f"Pusula yuvası Ø {fmt(pusula)} cm")

    # Kart yerleri
    for r, x, y, w, h, e in yer:
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.8)
        c.setDash(5, 3)
        c.rect(T.X(x), T.Y(y + h), T.L(w), T.L(h))
        c.setDash()
        c.setFillColorRGB(0.4, 0.4, 0.4)
        if e == "PROJE":
            c.setFont(FB, max(5, 15 * s))
            c.drawCentredString(T.X(x + w / 2), T.Y(y + h / 2 - 0.6), PROJE_ADI)
            c.setFont(F, max(4.5, 11 * s))
            c.drawCentredString(T.X(x + w / 2), T.Y(y + h / 2 + 0.3), ALT_BASLIK)
            c.setFont(F, max(4, 7 * s))
            c.drawCentredString(T.X(x + w / 2), T.Y(y + h / 2 + 1.5), "proje adı alanı (elle yazılır)")
            continue
        c.setFont(FB, max(6, 28 * s))
        c.drawCentredString(T.X(x + w / 2), T.Y(y + h / 2 - 0.2), r["id"])
        c.setFont(F, max(4.5, 10 * s))
        c.drawCentredString(T.X(x + w / 2), T.Y(y + h / 2 + 1.0), r["madde"])
        c.setFont(F, max(4, 7 * s))
        alt = "köşe kartı" if e == "KÖŞE" else YONLER[e]
        c.drawCentredString(T.X(x + w / 2), T.Y(y + h / 2 + 1.8), f"{alt} · {boyut_yazi((w, h))} cm")


def karolar():
    """Tabanı kaplayan A4 içerik karoları: [(satır_harf, sütun_no, ox, oy)]."""
    adim_x, adim_y = ALAN_W - BINDIRME, ALAN_H - BINDIRME
    nx = math.ceil((TABAN[0] - ALAN_W) / adim_x) + 1
    ny = math.ceil((TABAN[1] - ALAN_H) / adim_y) + 1
    return [("ABCDEFG"[j], i + 1, i * adim_x, j * adim_y) for j in range(ny) for i in range(nx)], nx, ny


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pusula", type=float, default=5.0, help="pusula yuvası çapı (cm)")
    a = ap.parse_args()

    rows = maddeleri_oku()
    yer = taban_yerlesimi(rows)
    kutular = [(e if r is None else r["id"], x, y, w, h) for r, x, y, w, h, e in yer]
    hatalar = kutular_denetle("Taban", TABAN, kutular)
    mx, my = TABAN_MERKEZ
    for etiket, x, y, w, h in kutular:  # pusula yuvasıyla çakışma
        en_yakin = math.hypot(max(x - mx, 0, mx - (x + w)), max(y - my, 0, my - (y + h)))
        if en_yakin < a.pusula / 2 + 1.5:
            hatalar.append(f"Taban: {etiket} pusula yuvasına çok yakın")
    if hatalar:
        raise SystemExit("\n".join(hatalar))

    os.makedirs(PRINT, exist_ok=True)
    yol = os.path.join(PRINT, "taban_ruzgar_gulu.pdf")
    c = canvas.Canvas(yol, pagesize=A4P)
    c.setTitle(f"{PROJE_ADI} — Taban şablonu 1:1")
    W, H = A4P
    k, nx, ny = karolar()

    # 1. sayfa: genel görünüş (1:5) ve birleştirme talimatı
    sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · Taban rüzgâr gülü · genel görünüş", 1)
    c.setFont(FB, 18)
    c.drawString(1.8 * cm, H - 2.4 * cm, "Taban şablonu (60×50 cm) — birleştirme planı")
    c.setFont(F, 10)
    c.drawString(1.8 * cm, H - 3.1 * cm, f"Aşağıdaki çizim 1:5 ölçeklidir. Sonraki {len(k)} sayfa 1:1 "
                 f"ölçekte; {ny} satır × {nx} sütun.")
    T = Donusum(0, 0, 4.5, 29.7 - 4.6, 0.2)
    taban_ciz(c, T, yer, a.pusula, izgara=False)
    c.setStrokeColorRGB(0.1, 0.35, 0.8)
    c.setFillColorRGB(0.1, 0.35, 0.8)
    c.setLineWidth(0.5)
    for harf, no, ox, oy in k:
        c.rect(T.X(ox) + 1, T.Y(oy + ALAN_H) + 1, T.L(ALAN_W) - 2, T.L(ALAN_H) - 2)
        c.setFont(FB, 9)
        c.drawString(T.X(ox) + 3, T.Y(oy) - 10, f"{harf}{no}")
    y = 29.7 - 4.6 - 10 - 1.4
    adimlar = [
        "Sayfaları %100 ölçekte bas; her sayfadaki 5 cm kontrol çizgisini cetvelle ölç.",
        f"Sayfalar komşularıyla {fmt(BINDIRME)} cm bindirilir (gri şerit). Sayfanın sağ ve alt kenarındaki "
        "beyaz boşluğu kes, sonra bir sonraki sayfanın gri şeridinin üstüne koy.",
        "Komşu sayfalardaki aynı koordinatlı + işaretlerini (ör. 20,20) üst üste getir ve kâğıt bantla "
        "yapıştır.",
        "Birleşen şablonu tabana koy; yön çizgilerini, kart yerlerini ve pusula yuvasını kopya kâğıdıyla "
        "ya da köşelerden iğneyle delip kurşun kalemle tabana aktar. Rüzgâr gülünü sonra elle boya.",
        "K (Yıldız) arka duvar tarafındadır. Sergide pusulaya bakıp kutuyu çevir: Yıldız kartı gerçek "
        "kuzeye bakınca bütün rüzgârlar gerçek yönlerini gösterir.",
    ]
    from common import satir_kir
    c.setFillColorRGB(0, 0, 0)
    for i, p in enumerate(adimlar, 1):
        for j, s in enumerate(satir_kir(p, F, 10, 16.8 * cm)):
            c.setFont(F, 10)
            c.drawString(1.8 * cm, y * cm, (f"{i}. " if j == 0 else "    ") + s)
            y -= 0.5
        y -= 0.15
    c.showPage()

    # 1:1 karolar
    for n, (harf, no, ox, oy) in enumerate(k, 2):
        sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · Taban 1:1 · Sayfa {harf}{no} "
                        f"(x {fmt(ox)}–{fmt(min(ox + ALAN_W, TABAN[0]))}, "
                        f"y {fmt(oy)}–{fmt(min(oy + ALAN_H, TABAN[1]))} cm)", n)
        c.saveState()
        p = c.beginPath()
        p.rect(KS * cm, (29.7 - KU - ALAN_H) * cm, ALAN_W * cm, ALAN_H * cm)
        c.clipPath(p, stroke=0, fill=0)
        # bindirme şeritleri (sol ve üst: önceki sayfanın altında kalacak kısım)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        if ox > 0:
            c.rect(KS * cm, (29.7 - KU - ALAN_H) * cm, BINDIRME * cm, ALAN_H * cm, stroke=0, fill=1)
        if oy > 0:
            c.rect(KS * cm, (29.7 - KU - BINDIRME) * cm, ALAN_W * cm, BINDIRME * cm, stroke=0, fill=1)
        T = Donusum(ox, oy, KS, 29.7 - KU, 1.0)
        taban_ciz(c, T, yer, a.pusula)
        c.restoreState()
        # içerik alanı sınırı (kesme kılavuzu)
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setLineWidth(0.3)
        c.rect(KS * cm, (29.7 - KU - ALAN_H) * cm, ALAN_W * cm, ALAN_H * cm)
        c.setFont(F, 6.5)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        komsu = []
        if ox > 0:
            komsu.append(f"sol şerit: {harf}{no - 1} altına")
        if oy > 0:
            komsu.append(f"üst şerit: {'ABCDEFG'[ord(harf) - 66]}{no} altına")
        if komsu:
            c.drawRightString((KS + ALAN_W) * cm, (29.7 - KU - ALAN_H - 0.35) * cm,
                              "Gri şerit → " + ", ".join(komsu))
        c.showPage()
    c.save()
    print(f"{os.path.relpath(yol)}: genel görünüş + {len(k)} adet 1:1 sayfa ({ny}×{nx}); "
          f"pusula yuvası Ø {fmt(a.pusula)} cm; çakışma yok")


if __name__ == "__main__":
    main()
