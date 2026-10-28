"""G10 — print/dizin_rehberi.pdf: 39 madde Türk alfabesine göre, okunur konumuyla."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from common import (A4P, ALFABE, F, FB, PRINT, PROJE_ADI, maddeleri_oku,  # noqa: E402
                    okunur_konum, sayfa_cercevesi, tr_lower, tr_sirala_anahtar)
from yerlesim import TABAN_KOSELER, duvar_yerlesimi, taban_yerlesimi  # noqa: E402

KOSE_AD = dict(zip(TABAN_KOSELER, ["arka sol köşe", "arka sağ köşe", "ön sol köşe"]))


def ayrintili_konum(r, sira):
    k = okunur_konum(r["konum"]).split(" (")[0]
    if r["id"] in sira:
        s, j = sira[r["id"]]
        if isinstance(s, str):
            k = f"Taban, {s}"
        else:
            k += f" — {s}. satır, {j}. kart"
    return k


def main():
    rows = maddeleri_oku()
    sira = {}
    for d in ("ARKA", "SOL", "SAG"):
        for r, *_, s, j in duvar_yerlesimi(d, rows)["kartlar"]:
            sira[r["id"]] = (s, j)
    for r, x, y, *_, e in taban_yerlesimi(rows):
        if e == "KÖŞE":
            sira[r["id"]] = (KOSE_AD[(x, y)], None)
    sirali = sorted(rows, key=lambda r: tr_sirala_anahtar(r["madde"]))

    os.makedirs(PRINT, exist_ok=True)
    yol = os.path.join(PRINT, "dizin_rehberi.pdf")
    c = canvas.Canvas(yol, pagesize=A4P)
    c.setTitle(f"{PROJE_ADI} — Dizin rehberi")
    W, H = A4P
    sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · Dizin rehberi", 1)
    c.setFont(FB, 18)
    c.drawString(1.8 * cm, H - 2.3 * cm, "Dizin — 39 madde, Türk alfabesine göre")
    c.setFont(F, 9)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(1.8 * cm, H - 2.9 * cm, "Dizin kartını buna bakarak elle yaz. Sıra: " + " ".join(ALFABE))
    c.setFillColorRGB(0, 0, 0)
    y = H - 3.9 * cm
    harf = None
    for r in sirali:
        ilk = tr_lower(r["madde"])[0].replace("â", "a")
        if ilk != harf:
            harf = ilk
            c.setFont(FB, 10)
            c.setFillColorRGB(0.45, 0.45, 0.45)
            c.drawString(1.8 * cm, y, harf.replace("i", "İ").upper() if harf == "i" else harf.upper())
            c.setFillColorRGB(0, 0, 0)
        c.setFont(FB, 10.5)
        c.drawString(2.6 * cm, y, r["madde"])
        c.setFont(F, 10.5)
        x = 2.6 * cm + c.stringWidth(r["madde"], FB, 10.5)
        konum = " — " + ayrintili_konum(r, sira)
        if x + c.stringWidth(konum, F, 10.5) > W - 2.3 * cm:  # sığmazsa alt satıra
            y -= 0.5 * cm
            x, konum = 3.2 * cm, konum[3:]
        c.drawString(x, y, konum)
        c.setFont(F, 7.5)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawRightString(W - 1.6 * cm, y, r["id"])
        c.setFillColorRGB(0, 0, 0)
        y -= 0.6 * cm
    c.showPage()
    c.save()
    print(f"{os.path.relpath(yol)}: {len(sirali)} madde")
    for r in sirali:
        print(f"  {r['madde']} — {ayrintili_konum(r, sira)}")


if __name__ == "__main__":
    main()
