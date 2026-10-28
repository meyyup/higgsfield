"""G5 — print/yerlesim_planlari.pdf: arka, sol ve sağ duvarların 1:5 ölçekli planı.

Kartlar sığmazsa common.KART_BOYUTU orantılı küçültür; değişiklikler ilk sayfada raporlanır.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from common import (A4P, ARALIK, DUVARLAR, F, FB, KART_BOYUTU, KART_BOYUTU_BRIF,  # noqa: E402
                    KENAR, PRINT, PROJE_ADI, boyut_yazi, fmt, maddeleri_oku, satir_kir,
                    sayfa_cercevesi)
from yerlesim import duvar_yerlesimi, kutular_denetle  # noqa: E402

OLCEK = 0.2  # 1:5
DUVAR_AD = {"ARKA": "Arka duvar", "SOL": "Sol duvar", "SAG": "Sağ duvar"}
GORUNUS = {
    "ARKA": "Önden bakan ziyaretçinin gördüğü gibi.",
    "SOL": "İçeriden bakıldığı gibi: sağ kenar arka duvara, sol kenar açık öne bakar.",
    "SAG": "İçeriden bakıldığı gibi: sol kenar arka duvara, sağ kenar açık öne bakar. "
           "Fırıldak bu duvarın dış üst kenarında, fan dış yüzde.",
}


def degisiklik_raporu():
    satirlar = []
    ad = {"ARKA-UST": "Arka duvar üst (12–21, 5×2)", "ARKA-ALT": "Arka duvar alt (22–27, tek sıra 6)",
          "SOL": "Sol duvar (28–32)", "SAG": "Sağ duvar (33–39)", "TABAN": "Taban (01–11)"}
    for k in ("TABAN", "ARKA-UST", "ARKA-ALT", "SOL", "SAG"):
        eski, yeni = KART_BOYUTU_BRIF[k], KART_BOYUTU[k]
        if eski != yeni:
            satirlar.append(f"{ad[k]}: {boyut_yazi(eski)} → {boyut_yazi(yeni)} cm (küçültüldü)")
        else:
            satirlar.append(f"{ad[k]}: {boyut_yazi(eski)} cm (değişmedi)")
    return satirlar


def ozet_sayfasi(c, sorunlar):
    W, H = A4P
    sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · Duvar yerleşim planları", 1)
    y = H - 2.6 * cm
    c.setFont(FB, 20)
    c.drawString(1.8 * cm, y, "Duvar yerleşim planları (1:5)")
    y -= 1.0 * cm
    c.setFont(F, 10.5)
    giris = (f"Ölçüler cm'dir. Kenar boşluğu en az {fmt(KENAR)} cm, kartlar arası en az {fmt(ARALIK)} cm. "
             "Her kartın konumu, duvarın SOL kenarından ve ÜST kenarından kartın sol üst köşesine olan "
             "uzaklıktır (planda kartın içinde ← soldan, ↑ üstten olarak da yazılıdır). Planlar 1:5 ölçeklidir (plandaki 1 cm = duvarda 5 cm); ölçüyü plandan cetvelle "
             "değil, tablodaki sayılardan alın.")
    for s in satir_kir(giris, F, 10.5, 17.4 * cm):
        c.drawString(1.8 * cm, y, s)
        y -= 0.52 * cm
    y -= 0.5 * cm
    c.setFont(FB, 13)
    c.drawString(1.8 * cm, y, "Kart boyutları ve küçültme raporu")
    y -= 0.65 * cm
    c.setFont(F, 10.5)
    for s in degisiklik_raporu():
        c.drawString(2.2 * cm, y, "•  " + s)
        y -= 0.52 * cm
    y -= 0.3 * cm
    neden = (f"Neden: arka duvar 60 cm; iki yanda {fmt(KENAR)} cm kenar kalınca kullanılabilir genişlik "
             f"{fmt(DUVARLAR['ARKA'][0] - 2 * KENAR)} cm. Üst sırada 5 adet 11 cm kart + 4 × {fmt(ARALIK)} cm "
             f"aralık = 61 cm; alt sırada 6 adet 9 cm kart + 5 × {fmt(ARALIK)} cm = 61,5 cm gerekiyordu. "
             "Kart genişliği 0,5 cm'ye aşağı yuvarlanıp yükseklik aynı oranda küçültüldü. "
             "Kart rehberleri (kart_rehberleri.pdf) ve maddeler.csv yeni ölçüleri kullanır. "
             "Alternatif: alt bölüm tek sıra yerine 3+3 dizilirse 9×12 cm korunabilir (yükseklik yeterli).")
    c.setFillColorRGB(0.25, 0.25, 0.25)
    for s in satir_kir(neden, F, 9.5, 17.4 * cm):
        c.setFont(F, 9.5)
        c.drawString(1.8 * cm, y, s)
        y -= 0.47 * cm
    c.setFillColorRGB(0, 0, 0)
    y -= 0.5 * cm
    c.setFont(FB, 13)
    c.drawString(1.8 * cm, y, "Denetim")
    y -= 0.65 * cm
    c.setFont(F, 10.5)
    if sorunlar:
        for s in sorunlar:
            c.drawString(2.2 * cm, y, "✗  " + s)
            y -= 0.5 * cm
    else:
        c.drawString(2.2 * cm, y, "✓  Bütün kartlar kenar ve aralık kurallarına uyuyor; çakışma yok.")
        y -= 0.5 * cm
    y -= 0.4 * cm
    c.setFillColorRGB(0.25, 0.25, 0.25)
    for s in satir_kir("Not: Duvar ölçüleri kolinin iç yüzü içindir. Koli kalınlığı ya da köşe "
                       "şeritleri iç ölçüyü birkaç mm küçültür; kenar boşlukları bunu karşılar. "
                       "Kutu boyutu öğretmenden teyit edilince planlar yeniden üretilebilir.",
                       F, 9.5, 17.4 * cm):
        c.setFont(F, 9.5)
        c.drawString(1.8 * cm, y, s)
        y -= 0.47 * cm
    c.showPage()


def duvar_sayfasi(c, duvar, yer, sayfa_no):
    W, H = A4P
    DW, DH = DUVARLAR[duvar]
    sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · {DUVAR_AD[duvar]} {fmt(DW)}×{fmt(DH)} cm · 1:5", sayfa_no)
    c.setFont(FB, 16)
    c.drawString(1.8 * cm, H - 2.2 * cm, f"{DUVAR_AD[duvar]} ({fmt(DW)} × {fmt(DH)} cm)")
    c.setFont(F, 9)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    for i, sat in enumerate(satir_kir(GORUNUS[duvar], F, 9, 17.4 * cm)):
        c.drawString(1.8 * cm, H - 2.75 * cm - i * 0.42 * cm, sat)
    c.setFillColorRGB(0, 0, 0)

    ox = (W / cm - DW * OLCEK) / 2 + 0.6
    oy = H / cm - 4.4  # duvarın üst kenarı (sayfa cm)

    def X(x):
        return (ox + x * OLCEK) * cm

    def Y(y):
        return (oy - y * OLCEK) * cm

    # Duvar
    c.setLineWidth(1.2)
    c.rect(X(0), Y(DH), DW * OLCEK * cm, DH * OLCEK * cm)
    c.setFont(F, 6.5)
    c.drawCentredString(X(DW / 2), Y(0) + 3, "üst kenar")
    c.drawCentredString(X(DW / 2), Y(DH) - 9, "taban")
    # Kenar boşluğu çizgisi
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.setLineWidth(0.4)
    c.setDash(1, 2)
    c.rect(X(KENAR), Y(DH - KENAR), (DW - 2 * KENAR) * OLCEK * cm, (DH - 2 * KENAR) * OLCEK * cm)
    c.setDash()

    # Başlık alanları
    for metin, x, y, w, h in yer["basliklar"]:
        c.setFillColorRGB(0.92, 0.92, 0.92)
        c.rect(X(x), Y(y + h), w * OLCEK * cm, h * OLCEK * cm, stroke=0, fill=1)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.setFont(FB, 7.5)
        c.drawCentredString(X(x + w / 2), Y(y + h / 2) - 2.5, f"Başlık: {metin}")
    # Dizin alanı
    if yer["dizin"]:
        x, y, w, h = yer["dizin"]
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setDash(3, 2)
        c.rect(X(x), Y(y + h), w * OLCEK * cm, h * OLCEK * cm)
        c.setDash()
        c.setFont(F, 6.5)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawCentredString(X(x + w / 2), Y(y + h / 2) + 2, "Dizin kartı (isteğe bağlı)")
        c.drawCentredString(X(x + w / 2), Y(y + h / 2) - 6, f"A5 {boyut_yazi((w, h))} cm")
    # Kartlar
    c.setStrokeColorRGB(0, 0, 0)
    for r, x, y, w, h, s, j in yer["kartlar"]:
        c.setLineWidth(0.7)
        c.setFillColorRGB(1, 1, 1)
        c.rect(X(x), Y(y + h), w * OLCEK * cm, h * OLCEK * cm, stroke=1, fill=0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont(FB, 10)
        c.drawCentredString(X(x + w / 2), Y(y + h / 2) - 1, r["id"])
        c.setFont(F, 5.5)
        c.drawCentredString(X(x + w / 2), Y(y + h / 2) - 10, f"←{fmt(x)}  ↑{fmt(y)}")

    # Ölçü zinciri: solda satırların üstten uzaklığı (sütunlar kart içinde yazılı)
    c.setLineWidth(0.4)
    c.setFont(F, 6)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    ys = sorted({y for _, _, y, *_ in yer["kartlar"]})
    for y in ys:
        c.line(X(0) - 12, Y(y), X(0) - 6, Y(y))
        c.drawRightString(X(0) - 14, Y(y) - 2, fmt(y))
    c.setFont(F, 6)
    c.drawRightString(X(0) - 14, Y(DH) - 10, "↑ üstten (cm)")

    # Ölçek çubuğu: 10 cm duvar = 2 cm plan
    c.setLineWidth(0.8)
    sx, sy = X(DW) + 10, Y(DH)
    c.line(sx, sy, sx, sy + 10 * OLCEK * cm)
    c.setFont(F, 6)
    c.drawString(sx + 3, sy + 5 * OLCEK * cm, "10 cm")

    # Tablo
    ty = oy - DH * OLCEK - 1.2
    c.setFont(FB, 9)
    kolon = [1.8, 2.8, 9.8, 12.0, 14.2, 16.4]
    for x, b in zip(kolon, ["ID", "Madde", "Soldan", "Üstten", "Boyut", "Satır/sıra"]):
        c.drawString(x * cm, ty * cm, b)
    ty -= 0.15
    c.setLineWidth(0.4)
    c.line(1.8 * cm, ty * cm, 19.2 * cm, ty * cm)
    c.setFont(F, 8.5)
    for r, x, y, w, h, s, j in yer["kartlar"]:
        ty -= 0.42
        madde = r["madde"] if len(r["madde"]) <= 38 else r["madde"][:36] + "…"
        for xx, v in zip(kolon, [r["id"], madde, f"{fmt(x)} cm", f"{fmt(y)} cm",
                                 f"{boyut_yazi((w, h))} cm", f"{s}. satır, {j}. kart"]):
            c.drawString(xx * cm, ty * cm, v)
    for metin, x, y, w, h in yer["basliklar"]:
        ty -= 0.42
        c.setFillColorRGB(0.35, 0.35, 0.35)
        c.drawString(kolon[0] * cm, ty * cm, "—")
        c.drawString(kolon[1] * cm, ty * cm, f"Başlık alanı: {metin}")
        c.drawString(kolon[2] * cm, ty * cm, f"{fmt(x)} cm")
        c.drawString(kolon[3] * cm, ty * cm, f"{fmt(y)} cm")
        c.drawString(kolon[4] * cm, ty * cm, f"{boyut_yazi((w, h))} cm")
    if yer["dizin"]:
        x, y, w, h = yer["dizin"]
        ty -= 0.42
        c.drawString(kolon[0] * cm, ty * cm, "—")
        c.drawString(kolon[1] * cm, ty * cm, "Dizin kartı (isteğe bağlı)")
        c.drawString(kolon[2] * cm, ty * cm, f"{fmt(x)} cm")
        c.drawString(kolon[3] * cm, ty * cm, f"{fmt(y)} cm")
        c.drawString(kolon[4] * cm, ty * cm, f"{boyut_yazi((w, h))} cm")
    c.setFillColorRGB(0, 0, 0)
    c.showPage()


def main():
    rows = maddeleri_oku()
    yerler, sorunlar = {}, []
    for d in ("ARKA", "SOL", "SAG"):
        yer = duvar_yerlesimi(d, rows)
        yerler[d] = yer
        kutular = [(r["id"], x, y, w, h) for r, x, y, w, h, *_ in yer["kartlar"]]
        kutular += [(f"başlık '{m}'", x, y, w, h) for m, x, y, w, h in yer["basliklar"]]
        if yer["dizin"]:
            kutular.append(("dizin", *yer["dizin"]))
        sorunlar += kutular_denetle(DUVAR_AD[d], DUVARLAR[d], kutular)

    os.makedirs(PRINT, exist_ok=True)
    yol = os.path.join(PRINT, "yerlesim_planlari.pdf")
    c = canvas.Canvas(yol, pagesize=A4P)
    c.setTitle(f"{PROJE_ADI} — Duvar yerleşim planları 1:5")
    ozet_sayfasi(c, sorunlar)
    for i, d in enumerate(("ARKA", "SOL", "SAG"), 2):
        duvar_sayfasi(c, d, yerler[d], i)
    c.save()
    print(f"{os.path.relpath(yol)}: özet + 3 duvar planı")
    for s in degisiklik_raporu():
        print("  " + s)
    if sorunlar:
        print("SORUN:\n  " + "\n  ".join(sorunlar))
        sys.exit(1)
    print("  Denetim: kenar ≥ 2 cm, aralık ≥ 1,5 cm, çakışma yok.")


if __name__ == "__main__":
    main()
