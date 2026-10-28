"""G9 — data/links.csv'den statik QR etiketleri: print/qr_etiketleri.pdf (+ print/qr/NN.png).

Hata düzeltme Q, 4 modül sessiz alan, 300 dpi'da 3×3 cm. Her QR geri okunur
(hem PNG hem basılacak PDF'in 300 dpi görüntüsü) ve URL ile birebir karşılaştırılır.
QR doğrudan YouTube linkini taşır; kısaltıcı ya da dinamik QR servisi kullanılmaz.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import qrcode  # noqa: E402
from PIL import Image  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from common import (A4P, DATA, F, FB, PRINT, PROJE_ADI, maddeleri_oku,  # noqa: E402
                    sayfa_cercevesi)

LINKS = os.path.join(DATA, "links.csv")
QR_CM = 3.0
DPI = 300
QR_PX = round(QR_CM / 2.54 * DPI)   # 354 px
URL_KALIPLARI = [
    r"^https://(www\.|m\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]{11}(&[^\s]*)?$",
    r"^https://youtu\.be/[A-Za-z0-9_-]{11}(\?[^\s]*)?$",
    r"^https://(www\.|m\.)?youtube\.com/shorts/[A-Za-z0-9_-]{11}(\?[^\s]*)?$",
]
# Etiket ızgarası (cm)
HUCRE_W, HUCRE_H, ARA = 3.0, 3.6, 0.9
KS, KU = 1.0, 1.6


def url_gecerli(u):
    return any(re.match(k, u) for k in URL_KALIPLARI)


def qr_png(url, yol):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=1, border=4)
    q.add_data(url)
    q.make(fit=True)
    moduller = q.modules_count + 8
    kutu = QR_PX // moduller
    if kutu < 3:
        raise ValueError(f"URL çok uzun: modül başına {kutu} px (300 dpi'da okunamayabilir)")
    q.box_size = kutu
    img = q.make_image(fill_color="black", back_color="white").convert("L")
    tuval = Image.new("L", (QR_PX, QR_PX), 255)   # artan pikseller sessiz alanı büyütür
    tuval.paste(img, ((QR_PX - img.width) // 2, (QR_PX - img.height) // 2))
    tuval.save(yol, dpi=(DPI, DPI))
    return q.version, kutu


def coz(gri):
    det = cv2.QRCodeDetector()
    metin, _, _ = det.detectAndDecode(gri)
    return metin


def main():
    rows = {r["id"]: r for r in maddeleri_oku()}
    if not os.path.exists(LINKS):
        raise SystemExit("data/links.csv yok; önce G8'i çalıştırıp linkleri doldurun.")
    with open(LINKS, encoding="utf-8-sig", newline="") as f:
        linkler = [(r["id"].strip().zfill(2), (r.get("url") or "").strip()) for r in csv.DictReader(f)]

    gecerli, sorunlar = [], []
    goruldu = set()
    for id_, url in linkler:
        if id_ not in rows:
            sorunlar.append(f"{id_}: maddeler.csv'de yok")
        elif id_ in goruldu:
            sorunlar.append(f"{id_}: links.csv'de birden fazla satır")
        elif not url:
            sorunlar.append(f"{id_}: url boş")
        elif not url_gecerli(url):
            sorunlar.append(f"{id_}: geçersiz URL biçimi ({url})")
        else:
            gecerli.append((id_, url))
        goruldu.add(id_)
    for id_ in rows:
        if id_ not in goruldu:
            sorunlar.append(f"{id_}: links.csv'de satır yok")

    qr_klasor = os.path.join(PRINT, "qr")
    os.makedirs(qr_klasor, exist_ok=True)
    sonuc = []
    for id_, url in gecerli:
        yol = os.path.join(qr_klasor, f"{id_}.png")
        try:
            surum, kutu = qr_png(url, yol)
        except ValueError as e:
            sorunlar.append(f"{id_}: {e}")
            continue
        okunan = coz(cv2.copyMakeBorder(cv2.imread(yol, cv2.IMREAD_GRAYSCALE), 20, 20, 20, 20,
                                        cv2.BORDER_CONSTANT, value=255))
        sonuc.append({"id": id_, "url": url, "png": yol, "surum": surum, "kutu": kutu,
                      "png_ok": okunan == url})

    if not sonuc:
        print("Üretilecek QR yok.")
        for s in sorunlar:
            print("  " + s)
        sys.exit(1)

    # PDF
    yol_pdf = os.path.join(PRINT, "qr_etiketleri.pdf")
    c = canvas.Canvas(yol_pdf, pagesize=A4P)
    c.setTitle(f"{PROJE_ADI} — QR etiketleri")
    W, H = A4P
    nx = int((W / cm - 2 * KS + ARA) // (HUCRE_W + ARA))
    ny = int((H / cm - KU - 1.6 + ARA) // (HUCRE_H + ARA))
    ox = (W / cm - (nx * HUCRE_W + (nx - 1) * ARA)) / 2
    yerler = {}
    for p in range(0, len(sonuc), nx * ny):
        sayfa = p // (nx * ny) + 1
        sayfa_cercevesi(c, A4P, f"{PROJE_ADI} · QR etiketleri (3×3 cm, statik, liste dışı YouTube)", sayfa)
        for k, s in enumerate(sonuc[p:p + nx * ny]):
            i, j = k % nx, k // nx
            x = ox + i * (HUCRE_W + ARA)
            y_ust = H / cm - KU - j * (HUCRE_H + ARA)
            c.drawImage(s["png"], x * cm, (y_ust - QR_CM) * cm, QR_CM * cm, QR_CM * cm)
            madde = rows[s["id"]]["madde"]
            etiket = f"{s['id']} · {madde}"
            punto = 7
            while c.stringWidth(etiket, F, punto) > HUCRE_W * cm and punto > 4.5:
                punto -= 0.5
            if c.stringWidth(etiket, F, punto) > HUCRE_W * cm:
                etiket = etiket[:28] + "…"
            c.setFont(F, punto)
            c.drawCentredString((x + HUCRE_W / 2) * cm, (y_ust - QR_CM - 0.33) * cm, etiket)
            # Kesim işaretleri (hücre köşelerinin dışında)
            c.setLineWidth(0.3)
            for kx in (x, x + HUCRE_W):
                for ky in (y_ust, y_ust - HUCRE_H):
                    sx = -1 if kx == x else 1
                    sy = 1 if ky == y_ust else -1
                    c.line((kx + sx * 0.1) * cm, ky * cm, (kx + sx * 0.35) * cm, ky * cm)
                    c.line(kx * cm, (ky + sy * 0.1) * cm, kx * cm, (ky + sy * 0.35) * cm)
            yerler[s["id"]] = (sayfa, x, y_ust)
        c.showPage()
    c.save()

    # Basılacak PDF'i 300 dpi'da görüntüye çevirip her QR'ı kendi yerinden yeniden oku
    with tempfile.TemporaryDirectory() as g:
        subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-png", yol_pdf, os.path.join(g, "s")],
                       check=True)
        sayfalar = sorted(os.listdir(g))
        for s in sonuc:
            sayfa, x, y_ust = yerler[s["id"]]
            img = cv2.imread(os.path.join(g, sayfalar[sayfa - 1]), cv2.IMREAD_GRAYSCALE)
            px = lambda v: int(round(v / 2.54 * DPI))  # noqa: E731
            ust = img.shape[0] - px(y_ust)
            kes = img[max(ust - 15, 0):ust + px(QR_CM) + 15, max(px(x) - 15, 0):px(x) + px(QR_CM) + 15]
            s["pdf_ok"] = coz(np.ascontiguousarray(kes)) == s["url"]

    tamam = [s for s in sonuc if s["png_ok"] and s["pdf_ok"]]
    rapor = [f"QR doğrulama: {len(tamam)}/{len(rows)} madde doğru URL'yi veriyor "
             f"({len(sonuc)} QR üretildi)"]
    for s in sonuc:
        durum = "OK" if s["png_ok"] and s["pdf_ok"] else \
            f"HATA (png={'ok' if s['png_ok'] else 'okunamadı'}, pdf={'ok' if s['pdf_ok'] else 'okunamadı'})"
        rapor.append(f"  {s['id']} {durum} · sürüm {s['surum']}, {s['kutu']} px/modül · {s['url']}")
    if sorunlar:
        rapor.append(f"Üretilmeyen ({len(sorunlar)}):")
        rapor += [f"  {x}" for x in sorunlar]
    metin = "\n".join(rapor)
    with open(os.path.join(PRINT, "qr_dogrulama.txt"), "w", encoding="utf-8") as f:
        f.write(metin + "\n")
    print(f"{os.path.relpath(yol_pdf)}")
    print(metin)
    if len(tamam) != len(sonuc):
        sys.exit(1)


if __name__ == "__main__":
    main()
