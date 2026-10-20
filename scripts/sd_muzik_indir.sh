#!/usr/bin/env bash
# Son Damla müzikleri: Kevin MacLeod (incompetech.com), CC BY 4.0. Kaynaklar assets/ses/KAYNAKLAR.md.
set -euo pipefail
cd "$(dirname "$0")/.."
K=assets/ses/kutuphane; mkdir -p $K
for t in "Heartwarming" "Volatile Reaction" "Lasting Hope" "Carefree"; do
  f="$K/${t// /_}.mp3"
  [ -f "$f" ] && continue
  u="https://incompetech.com/music/royalty-free/mp3-royaltyfree/${t// /%20}.mp3"
  echo "curl -sSL -o $f $u" >> out/komutlar.log
  curl -sSL -o "$f" "$u"
done
ls -la $K
