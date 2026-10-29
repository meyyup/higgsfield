#!/usr/bin/env python3
"""G4 — uploads/youtube_listesi.csv ve boş links.csv şablonu."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_shorts import slug  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

with (ROOT / "kelimeler.csv").open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

out = ROOT / "uploads" / "youtube_listesi.csv"
out.parent.mkdir(exist_ok=True)
with out.open("w", encoding="utf-8-sig", newline="") as f:   # BOM: Excel Türkçe karakterleri doğru açsın
    w = csv.writer(f)
    w.writerow(["id", "dosya_adi", "youtube_baslik", "youtube_aciklama", "oynatma_listesi",
                "gorunurluk", "kitle"])
    for r in rows:
        fn = f"{r['id']}_{slug(r['kelime'])}.mp4"
        assert (ROOT / "shorts" / fn).exists(), fn
        w.writerow([r["id"], fn, r["youtube_baslik"], r["youtube_aciklama"], r["kategori"],
                    "Liste dışı", "Çocuklar için yapıldı"])

links = ROOT / "links.csv"
if not links.exists():
    with links.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "url"])
        for r in rows:
            w.writerow([r["id"], ""])
print(f"{out.relative_to(ROOT)}: {len(rows)} satır")
