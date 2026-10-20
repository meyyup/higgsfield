#!/usr/bin/env bash
# Son Damla geçici seslendirme (edge-tts, tr-TR-EmelNeural). Gerçek kayıtlar assets/ses/sd_*.m4a olarak gelirse onlar kullanılır.
set -euo pipefail
cd "$(dirname "$0")/.."
T=work/tts; mkdir -p $T
say() { echo "edge-tts --voice tr-TR-EmelNeural --pitch=$3 --rate=$4 --text \"$2\" --write-media $T/$1.mp3" >> out/komutlar.log
        python3 scripts/edge_tts_proxy.py --voice tr-TR-EmelNeural --pitch="$3" --rate="$4" --text "$2" --write-media $T/$1.mp3; }
say sd_s1_damla "Ben Damla. Arkadaşlarımla yangınları söndürmekte çok zorlanıyoruz." +20Hz +10%
say sd_s2_pit   "Ne kadar yağsak da yetmiyor!" +55Hz +10%
say sd_s3_damla "Ormana atılan cam şişeler, mercek gibi güneşi topluyor ve yangın başlatabiliyor." +20Hz +0%
say sd_s4_damla "O yüzden, yangın söndürmediğimiz zamanlarda, cam şişeleri geri dönüşüm kutularına atıyoruz." +20Hz +5%
say sd_s5_pit   "Bu yaz hiç yangın çıkmadı!" +55Hz +10%
for f in $T/*.mp3; do printf "%s %s\n" "$(basename $f)" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f)"; done
