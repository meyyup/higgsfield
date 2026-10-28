"""G3 — print/kart_rehberleri.pdf: gerçek boyutta, YALNIZCA yol gösterici kart rehberleri.

Kural 1: kart yüzleri basılmaz. Bu sayfalar kesilip yapıştırılmak için değildir;
öğrenci yerleşim ve imla için bakar, kartı kraft kâğıda kendi eliyle yazar.
Bu yüzden her rehberin üstüne "REHBER — yapıştırmayın" filigranı basılır.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfbase.pdfmetrics import stringWidth  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from common import (A4L, A4P, ACIK_GRI, DOGRULANACAK, F, FB, PRINT, PROJE_ADI,  # noqa: E402
                    boyut_oku, boyut_yazi, fmt, maddeleri_oku, okunur_konum,
                    satir_kir, sayfa_cercevesi)

PAD = 0.4          # kart iç kenar boşluğu (cm)
QR = 3.0           # QR alanı (cm)
QR_KENAR = 0.3     # QR'ın kart kenarından uzaklığı (cm)
MIN_CIZIM = 2.5    # çizim alanı en az yüksekliği (cm)
METIN_RENK = (0.62, 0.62, 0.62)

KENAR_SOL, KENAR_SAG, KENAR_UST, KENAR_ALT = 0.8, 0.8, 1.2, 1.3
KART_ARASI = 0.7


class Kart:
    """Kart içi çizim: yerel koordinatlar cm, orijin sol üst, y aşağı."""

    def __init__(self, c, x, y_ust, w, h):
        self.c, self.x, self.y_ust, self.w, self.h = c, x, y_ust, w, h

    def X(self, x):
        return (self.x + x) * cm

    def Y(self, y):
        return (self.y_ust - y) * cm

    def kesim(self):
        c = self.c
        c.saveState()
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.setDash(4, 3)
        c.rect(self.X(0), self.Y(self.h), self.w * cm, self.h * cm)
        c.setDash()
        c.setLineWidth(0.4)
        for kx, ky in ((0, 0), (self.w, 0), (0, self.h), (self.w, self.h)):
            sx = -1 if kx == 0 else 1
            sy = -1 if ky == 0 else 1
            c.line(self.X(kx + sx * 0.1), self.Y(ky), self.X(kx + sx * 0.4), self.Y(ky))
            c.line(self.X(kx), self.Y(ky + sy * 0.1), self.X(kx), self.Y(ky + sy * 0.4))
        c.restoreState()

    def kesik_kutu(self, x, y, w, h, yazi=None, punto=6):
        c = self.c
        c.saveState()
        c.setStrokeColorRGB(*ACIK_GRI)
        c.setLineWidth(0.5)
        c.setDash(2, 2)
        c.rect(self.X(x), self.Y(y + h), w * cm, h * cm)
        if yazi:
            c.setFillColorRGB(*ACIK_GRI)
            c.setFont(F, punto)
            c.drawCentredString(self.X(x + w / 2), self.Y(y + h / 2) - punto / 3, yazi)
        c.restoreState()

    def qr_ust(self):
        return self.h - QR_KENAR - QR

    def qr_kutu(self):
        self.kesik_kutu(self.w - QR_KENAR - QR, self.qr_ust(), QR, QR, "QR 3×3 cm")


def kelime_satirlari(madde, w):
    """Kelimeyi kart genişliğine sığacak en büyük puntoda (en çok 3 satır) böl."""
    gen = (w - 2 * PAD) * cm
    for punto in range(24, 9, -1):
        satirlar = satir_kir(madde, FB, punto, gen)
        if len(satirlar) <= 3 and all(stringWidth(s, FB, punto) <= gen for s in satirlar):
            return punto, satirlar
    return 10, satir_kir(madde, FB, 10, gen)


def paragraflar(r):
    etiket = "Anlam" if r["tur"] in ("Deyim", "Atasözü") else "Köken"
    p = [r["cumle"], f"{etiket}: {r['koken']}"]
    if r["alinti"]:
        p.append(f"Eski metin: {r['alinti']}")
    return p


def metin_yerlesimi(paras, punto, ust, w, h):
    """ust (cm) noktasından başlayarak satırları yerleştir; QR hizasında satır daralır."""
    lh = punto * 1.25 / 28.3465  # satır yüksekliği (cm)
    tam = (w - 2 * PAD) * cm
    dar = (w - PAD - QR - QR_KENAR - 0.25) * cm
    qr_ust = h - QR_KENAR - QR
    y = ust
    cikti = []
    for i, p in enumerate(paras):
        if i:
            y += 0.12
        kelimeler = p.split()
        mevcut = ""
        for k in kelimeler:
            gen = tam if y + lh <= qr_ust - 0.1 else dar
            aday = f"{mevcut} {k}".strip()
            if stringWidth(aday, F, punto) <= gen or not mevcut:
                mevcut = aday
            else:
                y += lh
                cikti.append((y, mevcut))
                mevcut = k
        if mevcut:
            y += lh
            cikti.append((y, mevcut))
    return cikti, y


def rehber_kart(c, x, y_ust, r):
    w, h = boyut_oku(r["kart_boyutu"])
    k = Kart(c, x, y_ust, w, h)
    k.kesim()
    filigran(c, k)

    # Küçük künye (sol üst köşe, kesim çizgisinin içinde)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.setFont(F, 5.5)
    c.drawString(k.X(PAD), k.Y(0.32), f"{r['id']} · {okunur_konum(r['konum']).split(' (')[0]} · "
                 f"{boyut_yazi(boyut_oku(r['kart_boyutu']))} cm")

    # Kelime
    punto, satirlar = kelime_satirlari(r["madde"], w)
    c.setFillColorRGB(*METIN_RENK)
    c.setFont(FB, punto)
    y = 0.45
    lh = punto * 1.15 / 28.3465
    for s in satirlar:
        y += lh
        c.drawCentredString(k.X(w / 2), k.Y(y - 0.08), s)
    kelime_alt = y + 0.15

    # Alt metin: en büyük puntoyu ve çizime en çok yeri bırakan yerleşimi bul
    paras = paragraflar(r)
    alt_sinir = h - PAD
    secilen = None
    for punto10 in range(90, 49, -5):
        punto = punto10 / 10
        ust = alt_sinir
        while ust > kelime_alt + MIN_CIZIM:
            satirlar, son = metin_yerlesimi(paras, punto, ust, w, h)
            if son <= alt_sinir:
                break
            ust -= 0.05
        if son <= alt_sinir and ust - kelime_alt - 0.25 >= MIN_CIZIM:
            secilen = (punto, ust, satirlar)
            break
    if secilen is None:
        raise SystemExit(f"{r['id']} kartına metin sığmadı ({r['kart_boyutu']})")
    punto, ust, satirlar = secilen

    # Çizim alanı
    cizim_ust = kelime_alt + 0.05
    cizim_h = ust - 0.2 - cizim_ust
    k.kesik_kutu(PAD, cizim_ust, w - 2 * PAD, cizim_h)
    c.setFillColorRGB(*ACIK_GRI)
    c.setFont(F, 6.5)
    for i, s in enumerate(satir_kir(f"Çizim: {r['cizim']}", F, 6.5, (w - 2 * PAD - 0.6) * cm)):
        c.drawCentredString(k.X(w / 2), k.Y(cizim_ust + cizim_h / 2 + i * 0.3), s)
    if r["id"] in DOGRULANACAK:
        c.setFillColorRGB(0.8, 0.15, 0.1)
        c.setFont(FB, 6)
        uyari = f"! Karta yazmadan önce doğrula: {DOGRULANACAK[r['id']]}"
        for i, s in enumerate(satir_kir(uyari, FB, 6, (w - 2 * PAD - 0.3) * cm)):
            c.drawString(k.X(PAD + 0.15), k.Y(cizim_ust + 0.35 + i * 0.27), s)

    # Metin
    c.setFillColorRGB(*METIN_RENK)
    c.setFont(F, punto)
    for yy, s in satirlar:
        c.drawString(k.X(PAD), k.Y(yy - 0.05), s)
    k.qr_kutu()


def filigran(c, k):
    c.saveState()
    c.setFillColorRGB(0.93, 0.93, 0.93)
    c.setFont(FB, 15)
    c.translate(k.X(k.w / 2), k.Y(k.h / 2))
    c.rotate(55)
    c.drawCentredString(0, -5, "REHBER · YAPIŞTIRMA")
    c.restoreState()


def bos_sablon(c, x, y_ust, w, h):
    k = Kart(c, x, y_ust, w, h)
    k.kesim()
    k.kesik_kutu(PAD, PAD, w - 2 * PAD, 1.5, "kelime", 7)
    cizim_h = (h - PAD - 1.5 - 0.3) * 0.5
    k.kesik_kutu(PAD, PAD + 1.5 + 0.3, w - 2 * PAD, cizim_h, "çizim", 7)
    c.saveState()
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.setLineWidth(0.4)
    y = PAD + 1.5 + 0.3 + cizim_h + 0.6
    while y <= h - PAD:
        sag = w - PAD if y < k.qr_ust() - 0.1 else w - QR - QR_KENAR - 0.3
        c.line(k.X(PAD), k.Y(y), k.X(sag), k.Y(y))
        y += 0.6
    c.restoreState()
    k.qr_kutu()
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.setFont(F, 6)
    c.drawString(k.X(PAD), k.Y(0.3), f"Boş şablon {boyut_yazi((w, h))} cm")


def yerlesim(w, h):
    """Bu boyuttaki kart için en çok kartı alan sayfa yönü ve konumları."""
    en_iyi = None
    for boyu in (A4P, A4L):
        W, H = boyu[0] / cm, boyu[1] / cm
        kullan_w = W - KENAR_SOL - KENAR_SAG
        kullan_h = H - KENAR_UST - KENAR_ALT
        nx = int((kullan_w + KART_ARASI) // (w + KART_ARASI))
        ny = int((kullan_h + KART_ARASI) // (h + KART_ARASI))
        if nx * ny and (en_iyi is None or nx * ny > en_iyi[0]):
            ox = KENAR_SOL + (kullan_w - (nx * w + (nx - 1) * KART_ARASI)) / 2
            oy = KENAR_UST + (kullan_h - (ny * h + (ny - 1) * KART_ARASI)) / 2
            konumlar = [(ox + i * (w + KART_ARASI), H - (oy + j * (h + KART_ARASI)))
                        for j in range(ny) for i in range(nx)]
            en_iyi = (nx * ny, boyu, konumlar)
    if en_iyi is None:
        raise SystemExit(f"{boyut_yazi((w, h))} kart A4'e sığmıyor")
    return en_iyi[1], en_iyi[2]


def giris_sayfasi(c, rows, boyutlar):
    W, H = A4P
    sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · Kart rehberleri", 1)
    y = H - 2.6 * cm
    c.setFont(FB, 22)
    c.drawString(1.8 * cm, y, "Kart rehberleri — yalnızca yol göstericidir")
    y -= 1.1 * cm
    metin = [
        "Bu sayfalar kartın kendisi DEĞİLDİR; kesip yapıştırmayın.",
        "Kartları kraft kâğıda ya da krem kartona kendi elinle yazar ve çizersin. Rehberlere yalnızca "
        "yerleşime ve imlaya bakmak için kullan: kelime üstte, çizim ortada, örnek cümle ve köken altta, "
        "sağ alt köşede 3×3 cm QR yeri boş kalır (QR etiketi videolar yüklendikten sonra yapıştırılır).",
        "Kenar ölçüsünü almak için rehberi kraft kâğıdın üstüne koyup köşe işaretlerinden kurşun kalemle "
        "işaretleyebilir ya da en sondaki boş kesim şablonlarını kalıp olarak kullanabilirsin.",
        "Kırmızı \"doğrula\" uyarısı olan maddelerin kökenini Nişanyan Sözlük ya da TDK'dan kontrol "
        "etmeden karta yazma (proje kuralı 5).",
    ]
    for p in metin:
        for s in satir_kir(p, F, 11, 17.4 * cm):
            c.setFont(F, 11)
            c.drawString(1.8 * cm, y, s)
            y -= 0.55 * cm
        y -= 0.25 * cm
    y -= 0.3 * cm
    c.setFont(FB, 13)
    c.drawString(1.8 * cm, y, "Kart boyutları")
    y -= 0.6 * cm
    c.setFont(F, 10.5)
    for ad, b, ids in boyutlar:
        c.drawString(2.2 * cm, y, f"{ad}: {boyut_yazi(b)} cm  ({ids})")
        y -= 0.5 * cm
    y -= 0.4 * cm
    c.setFont(FB, 13)
    c.drawString(1.8 * cm, y, "Karta yazmadan önce doğrulanacak maddeler")
    y -= 0.6 * cm
    ad = {r["id"]: r["madde"] for r in rows}
    c.setFont(F, 10)
    for id_ in sorted(DOGRULANACAK):
        c.drawString(2.2 * cm, y, f"☐  {id_} {ad[id_]} — {DOGRULANACAK[id_]}")
        y -= 0.47 * cm
    c.showPage()


def main():
    rows = maddeleri_oku()
    os.makedirs(PRINT, exist_ok=True)
    yol = os.path.join(PRINT, "kart_rehberleri.pdf")
    c = canvas.Canvas(yol, pagesize=A4P)
    c.setTitle(f"{PROJE_ADI} — Kart rehberleri (yol gösterici)")

    bolum_ad = {"TABAN": "Taban", "ARKA-UST": "Arka duvar üst", "ARKA-ALT": "Arka duvar alt",
                "SOL": "Sol duvar", "SAG": "Sağ duvar"}
    gruplar = {}
    for r in rows:
        b = r["konum"].split("-")[0] if r["konum"].startswith("TABAN") else r["konum"]
        gruplar.setdefault(b, []).append(r)
    boyutlar = [(bolum_ad[b], boyut_oku(g[0]["kart_boyutu"]), f"{g[0]['id']}–{g[-1]['id']}")
                for b, g in gruplar.items()]
    giris_sayfasi(c, rows, boyutlar)

    sayfa = 2
    for b, grup in gruplar.items():
        w, h = boyut_oku(grup[0]["kart_boyutu"])
        boyu, konumlar = yerlesim(w, h)
        for p in range(0, len(grup), len(konumlar)):
            parca = grup[p:p + len(konumlar)]
            c.setPageSize(boyu)
            sayfa_cercevesi(c, boyu, f"{PROJE_ADI} · Kart rehberi · {bolum_ad[b]} · "
                            f"{parca[0]['id']}–{parca[-1]['id']} · {fmt(w)}×{fmt(h)} cm · "
                            "YOL GÖSTERİCİ — YAPIŞTIRMAYIN", sayfa)
            for (x, y), r in zip(konumlar, parca):
                rehber_kart(c, x, y, r)
            c.showPage()
            sayfa += 1

    # Her kart boyutu için boş kesim şablonu
    goruldu = []
    for ad, b, _ in boyutlar:
        if b in goruldu:
            continue
        goruldu.append(b)
        boyu, konumlar = yerlesim(*b)
        c.setPageSize(boyu)
        sayfa_cercevesi(c, boyu, f"{PROJE_ADI} · Boş kesim şablonu · {boyut_yazi(b)} cm", sayfa)
        for x, y in konumlar:
            bos_sablon(c, x, y, *b)
        c.showPage()
        sayfa += 1
    c.save()
    print(f"{os.path.relpath(yol)}: {sayfa - 1} sayfa ({len(rows)} rehber kart + "
          f"{len(goruldu)} boş şablon sayfası)")


if __name__ == "__main__":
    main()
