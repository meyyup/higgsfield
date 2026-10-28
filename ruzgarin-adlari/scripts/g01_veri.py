"""G1 — BRIEF.md bölüm 3 ve 4 tablolarından data/maddeler.csv üretir ve doğrular."""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (CSV_PATH, ROOT, SUTUNLAR, TURKCE_TEST, boyut_yazi,  # noqa: E402
                    kart_boyutu, slugla)

BRIEF = os.path.join(ROOT, "BRIEF.md")
KONUM_KODLARI = {f"TABAN-{k}" for k in ("K", "KD", "D", "GD", "G", "GB", "B", "KB", "KOSE")} | {
    "ARKA-UST", "ARKA-ALT", "SOL", "SAG"}


def bolum_tablosu(satirlar, baslik_on_eki):
    """`## <n>.` ile başlayan bölümdeki ilk Markdown tablosunu satır listesi olarak döndürür."""
    icinde, tablo = False, []
    for s in satirlar:
        if s.startswith("## "):
            if icinde and tablo:
                break
            icinde = s.startswith(baslik_on_eki)
            continue
        if icinde and s.startswith("|"):
            hucreler = [h.strip() for h in s.strip().strip("|").split(" | ")]
            tablo.append(hucreler)
        elif icinde and tablo:
            break
    if len(tablo) < 3:
        raise SystemExit(f"{baslik_on_eki} tablosu bulunamadı")
    return tablo[0], tablo[2:]  # başlık, (ayırıcıyı atla) veri


def bos_ise(s):
    return "" if s in ("—", "-", "") else s


def main():
    with open(BRIEF, encoding="utf-8") as f:
        satirlar = f.read().splitlines()

    b3, veri3 = bolum_tablosu(satirlar, "## 3.")
    b4, veri4 = bolum_tablosu(satirlar, "## 4.")
    assert len(b3) == 8 and len(b4) == 4, (b3, b4)
    ses = {r[0]: r for r in veri4}

    kayitlar, hatalar = [], []
    for r in veri3:
        if len(r) != 8:
            hatalar.append(f"Bölüm 3 satırı 8 sütun değil: {r[:2]}")
            continue
        id_, madde, tur, konum, cumle, koken, alinti, cizim = r
        if konum not in KONUM_KODLARI:
            hatalar.append(f"{id_}: bilinmeyen konum {konum}")
        s = ses.get(id_)
        if not s or s[1] != madde:
            hatalar.append(f"{id_}: bölüm 4'te eşleşen satır yok ya da madde adı farklı")
            s = [id_, madde, "", ""]
        kayitlar.append({
            "id": id_, "slug": slugla(id_, madde), "madde": madde, "tur": tur,
            "konum": konum, "kart_boyutu": boyut_yazi(kart_boyutu(konum)),
            "cumle": cumle, "koken": koken, "alinti": bos_ise(alinti), "cizim": cizim,
            "seslendirme": s[2], "prompt": s[3],
        })

    # Kontroller
    idler = [k["id"] for k in kayitlar]
    if len(kayitlar) != 39:
        hatalar.append(f"Satır sayısı 39 değil: {len(kayitlar)}")
    if len(set(idler)) != len(idler):
        hatalar.append("Tekrarlanan id var")
    if idler != [f"{i:02d}" for i in range(1, len(idler) + 1)]:
        hatalar.append("ID'ler 01'den başlayıp sıralı ve iki haneli değil")
    zorunlu = [c for c in SUTUNLAR if c != "alinti"]
    for k in kayitlar:
        for c in zorunlu:
            if not k[c].strip():
                hatalar.append(f"{k['id']}: boş zorunlu alan '{c}'")
    if hatalar:
        print("HATA:\n  " + "\n  ".join(hatalar))
        sys.exit(1)

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUTUNLAR)
        w.writeheader()
        w.writerows(kayitlar)

    # Geri okuma: Türkçe karakterler bozulmadı mı?
    with open(CSV_PATH, encoding="utf-8") as f:
        icerik = f.read()
    bulunan = sorted(set(ch for ch in "çğıİöşüâÇĞÖŞÜ" if ch in icerik))
    assert "�" not in icerik and "Ã" not in icerik, "Kodlama bozulması var"
    print(f"data/maddeler.csv: {len(kayitlar)} satır, benzersiz id, boş zorunlu alan yok.")
    print(f"Türkçe karakterler korunuyor: {' '.join(bulunan)} (test dizisi: {TURKCE_TEST})")


if __name__ == "__main__":
    main()
