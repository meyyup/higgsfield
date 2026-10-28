#!/usr/bin/env bash
# Hemen üretilebilen çıktılar: G1–G5, G10, G11 (BRIEF.md -> data/ ve print/)
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/g01_veri.py
python3 scripts/g02_kayit_kiti.py
python3 scripts/g03_kart_rehberleri.py
python3 scripts/g04_taban.py "$@"
python3 scripts/g05_yerlesim_planlari.py
python3 scripts/g10_dizin.py > /dev/null && echo "print/dizin_rehberi.pdf: 39 madde"
python3 scripts/g11_promptlar.py
python3 scripts/g08_yukleme_listesi.py > /dev/null  # data/links.csv şablonu
python3 scripts/kontrol.py
