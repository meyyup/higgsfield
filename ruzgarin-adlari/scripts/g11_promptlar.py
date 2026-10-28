"""G11 — data/higgsfield_promptlari.txt: stil satırı + her maddenin yedek görsel promptu."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, STIL, maddeleri_oku  # noqa: E402


def main():
    rows = maddeleri_oku()
    yol = os.path.join(DATA, "higgsfield_promptlari.txt")
    with open(yol, "w", encoding="utf-8") as f:
        f.write("# Rüzgârın Adları — yedek görsel promptları (Higgsfield)\n")
        f.write("# YALNIZCA kartın el çizimi fotoğrafı (media/images/NN.jpg) yoksa kullanılır.\n")
        f.write("# Her promptun başına aşağıdaki stil satırı eklenir.\n\n")
        f.write(f"STIL: {STIL}\n\n")
        for r in rows:
            f.write(f"{r['id']} {r['madde']}: {STIL} {r['prompt']}\n")
    print(f"{os.path.relpath(yol)}: {len(rows)} prompt")


if __name__ == "__main__":
    main()
