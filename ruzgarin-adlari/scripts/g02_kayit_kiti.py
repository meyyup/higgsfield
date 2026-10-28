"""G2 — print/seslendirme_metinleri.pdf: kayıt talimatı + sayfa başına 4 metin."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from common import (A4P, F, FB, PRINT, PROJE_ADI, maddeleri_oku,  # noqa: E402
                    satir_kir, sayfa_cercevesi)

PUNTO = 18
SATIR = PUNTO * 1.35


def kapak(c, W, H):
    sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · Seslendirme metinleri", 1)
    y = H - 3 * cm
    c.setFont(FB, 26)
    c.drawString(2 * cm, y, "Seslendirme kayıt kiti")
    y -= 1.3 * cm
    c.setFont(F, 15)
    c.drawString(2 * cm, y, "39 metin · tek oturumda yaklaşık 15 dakika")
    y -= 1.8 * cm
    c.setFont(FB, 17)
    c.drawString(2 * cm, y, "Kayıttan önce")
    y -= 0.4 * cm
    maddeler = [
        "Sessiz bir oda seç; kapıyı ve pencereyi kapat, fanı/klimayı kapat.",
        "Telefonu ağzından yaklaşık 20 cm uzakta tut (bir karış kadar).",
        "Telefonu uçak moduna al; bildirim sesi kayda girmesin.",
        "Önce 1 deneme kaydı yap, dinle; ses çok kısık ya da cızırtılıysa yaklaş/uzaklaş.",
    ]
    for m in maddeler:
        for i, s in enumerate(satir_kir(m, F, 14, 16 * cm)):
            y -= 0.75 * cm
            c.setFont(F, 14)
            c.drawString(2.6 * cm, y, ("•  " if i == 0 else "    ") + s)
    y -= 1.3 * cm
    c.setFont(FB, 17)
    c.drawString(2 * cm, y, "Her kayıtta")
    y -= 0.4 * cm
    maddeler = [
        "Kayda bas, 1 saniye sus, metni oku, 1 saniye sus, kaydı durdur.",
        "Her metin ayrı bir kayıt olsun. Dosyayı kutudaki adla kaydet (ör. 06.m4a).",
        "Yanlış okursan dur ve o metni baştan yeniden kaydet.",
        "Acele etme; anlatır gibi, sakin ve açık oku. Bitince kutucuğu işaretle.",
    ]
    for m in maddeler:
        for i, s in enumerate(satir_kir(m, F, 14, 16 * cm)):
            y -= 0.75 * cm
            c.setFont(F, 14)
            c.drawString(2.6 * cm, y, ("•  " if i == 0 else "    ") + s)
    y -= 1.5 * cm
    c.setFont(F, 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    for s in satir_kir("Kayıtlar media/audio/ klasörüne 01.m4a … 39.m4a adlarıyla konur. "
                       "Seslendirme senin kendi sesin olmalı; yapay ses kullanılmaz.",
                       F, 12, 17 * cm):
        c.drawString(2 * cm, y, s)
        y -= 0.6 * cm
    c.showPage()


def main():
    rows = maddeleri_oku()
    os.makedirs(PRINT, exist_ok=True)
    yol = os.path.join(PRINT, "seslendirme_metinleri.pdf")
    W, H = A4P
    c = canvas.Canvas(yol, pagesize=A4P)
    c.setTitle(f"{PROJE_ADI} — Seslendirme metinleri")
    kapak(c, W, H)

    sol, sag = 1.8 * cm, W - 1.8 * cm
    blok_y = (H - 1.4 * cm - 1.4 * cm) / 4  # 4 metin / sayfa
    for p in range(0, len(rows), 4):
        sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · Seslendirme metinleri", p // 4 + 2)
        for i, r in enumerate(rows[p:p + 4]):
            ust = H - 1.4 * cm - i * blok_y
            if i:
                c.setStrokeColorRGB(0.75, 0.75, 0.75)
                c.setDash(3, 3)
                c.line(sol, ust, sag, ust)
                c.setDash()
            y = ust - 1.1 * cm
            c.setFillColorRGB(0, 0, 0)
            c.setFont(FB, 20)
            c.drawString(sol, y, f"{r['id']}  ·  {r['madde']}")
            c.setFont(FB, 14)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawRightString(sag - 1 * cm, y, f"Dosya: {r['id']}.m4a")
            c.setStrokeColorRGB(0, 0, 0)
            c.rect(sag - 0.6 * cm, y - 0.1 * cm, 0.55 * cm, 0.55 * cm)  # kutucuk
            y -= 0.5 * cm
            c.setFillColorRGB(0, 0, 0)
            punto = PUNTO
            while True:
                satirlar = satir_kir(r["seslendirme"], F, punto, sag - sol)
                if len(satirlar) * punto * 1.35 <= blok_y - 2 * cm or punto <= 13:
                    break
                punto -= 1
            c.setFont(F, punto)
            for s in satirlar:
                y -= punto * 1.35
                c.drawString(sol, y, s)
        c.showPage()
    c.save()
    print(f"{os.path.relpath(yol)}: kapak + {-(-len(rows) // 4)} metin sayfası")


if __name__ == "__main__":
    main()
