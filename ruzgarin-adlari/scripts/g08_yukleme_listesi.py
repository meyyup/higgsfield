"""G8 — uploads/youtube_listesi.csv ve (yoksa) data/links.csv şablonu.

Yüklemeyi veli elle yapar; görünürlük: Liste dışı (unlisted). Yüklemeden sonra
her videonun linki data/links.csv dosyasına (id,url) yazılır.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ALT_BASLIK, DATA, PROJE_ADI, UPLOADS, VIDEOS, maddeleri_oku  # noqa: E402

LINKS = os.path.join(DATA, "links.csv")


def main():
    rows = maddeleri_oku()
    os.makedirs(UPLOADS, exist_ok=True)
    yol = os.path.join(UPLOADS, "youtube_listesi.csv")
    var, yok = [], []
    for r in rows:
        dosya = f"{r['slug']}.mp4"
        (var if os.path.exists(os.path.join(VIDEOS, dosya)) else yok).append((r, dosya))
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "dosya", "baslik", "aciklama", "gorunurluk"])
        for r, dosya in var:
            w.writerow([r["id"], dosya, f"{r['madde']} — {PROJE_ADI}",
                        f"{PROJE_ADI} · {ALT_BASLIK} projesinden \"{r['madde']}\" maddesi; "
                        "seslendirme öğrencinin kendi sesidir.",
                        "Liste dışı"])
    print(f"{os.path.relpath(yol)}: {len(var)} video")
    if yok:
        print(f"Videosu henüz olmayan {len(yok)} madde listeye alınmadı: "
              + ", ".join(r["id"] for r, _ in yok))

    if not os.path.exists(LINKS):
        with open(LINKS, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "url"])
            for r in rows:
                w.writerow([r["id"], ""])
        print(f"{os.path.relpath(LINKS)}: boş şablon oluşturuldu (yüklemeden sonra url sütununu doldurun)")


if __name__ == "__main__":
    main()
