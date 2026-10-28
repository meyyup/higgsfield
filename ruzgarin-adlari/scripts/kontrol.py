"""Kabul kriterleri denetimi (bölüm 5): CSV, Türkçe karakter/font kapsamı, PDF sayfaları, videolar."""
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (BASKI_NOTU, PRINT, VIDEOS, font_kapsami_kontrol,  # noqa: E402
                    maddeleri_oku)

PDFLER = ["seslendirme_metinleri.pdf", "kart_rehberleri.pdf", "taban_ruzgar_gulu.pdf",
          "yerlesim_planlari.pdf", "dizin_rehberi.pdf", "qr_etiketleri.pdf"]


def sonuc(ok, metin):
    print(("  ✓ " if ok else "  ✗ ") + metin)
    return ok


def main():
    hepsi = True
    print("1. maddeler.csv")
    rows = maddeleri_oku()
    hepsi &= sonuc(len(rows) == 39 and len({r["id"] for r in rows}) == 39, f"{len(rows)} satır, benzersiz id")
    metin = "".join(v for r in rows for v in r.values())
    hepsi &= sonuc(all(ch in metin for ch in "çğıİöşüâ"), "Türkçe karakterler (ç ğ ı İ ö ş ü â) mevcut")
    eksik = font_kapsami_kontrol(metin + "%·—…×←↑☐✓✗")
    hepsi &= sonuc(not eksik, "font bütün karakterleri kapsıyor" + (f" — eksik: {eksik}" if eksik else ""))

    print("2. PDF'ler (A4, her sayfada baskı notu ve 5 cm kontrol çizgisi)")
    for ad in PDFLER:
        yol = os.path.join(PRINT, ad)
        if not os.path.exists(yol):
            print(f"  – {ad}: henüz yok")
            continue
        bilgi = subprocess.run(["pdfinfo", "-f", "1", "-l", "999", yol], capture_output=True, text=True).stdout
        boyutlar = {s.split(":", 1)[1].split("pts")[0].strip() for s in bilgi.splitlines()
                    if s.startswith("Page") and "size" in s}
        a4 = all(sorted(map(float, b.split(" x "))) == [595.276, 841.89] for b in boyutlar)
        sayfa = subprocess.run(["pdftotext", "-layout", yol, "-"], capture_output=True, text=True).stdout
        sayfalar = [s for s in sayfa.split("\f") if s.strip()]
        notlu = sum(1 for s in sayfalar if BASKI_NOTU in s and "5 cm kontrol" in s)
        hepsi &= sonuc(a4 and notlu == len(sayfalar),
                       f"{ad}: {len(sayfalar)} sayfa, A4={'evet' if a4 else 'HAYIR'}, not+çizgi {notlu}/{len(sayfalar)}")

    print("3. Videolar (8–25 sn, 1080×1920, 30 fps, H.264 + AAC)")
    vids = sorted(glob.glob(os.path.join(VIDEOS, "[0-9][0-9]_*.mp4")))
    if not vids:
        print("  – henüz video yok")
    for v in vids:
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "stream=codec_name,width,height,r_frame_rate:format=duration",
                            "-of", "default=nw=1", v], capture_output=True, text=True).stdout
        d = dict(s.split("=", 1) for s in p.splitlines() if "=" in s)
        ok = ("h264" in p and "aac" in p and d.get("width") == "1080" and d.get("height") == "1920"
              and "30/1" in p and 7.95 <= float(d.get("duration", 0)) <= 25.05)
        hepsi &= sonuc(ok, f"{os.path.basename(v)}: {float(d.get('duration', 0)):.1f} sn")
    print("\nSONUÇ: " + ("hepsi geçti" if hepsi else "SORUN VAR"))
    sys.exit(0 if hepsi else 1)


if __name__ == "__main__":
    main()
