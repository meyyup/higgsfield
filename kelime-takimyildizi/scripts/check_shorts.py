#!/usr/bin/env python3
"""Kabul kontrolü: 30 ses / görsel / Shorts, 1080×1920, 30 fps, ≤40 sn, H.264+AAC,
fontta Türkçe glifler, altyazı metninin seslendirmeyle birebir eşleşmesi. Rapor: shorts/kontrol.md"""
import csv
import json
import pathlib
import subprocess
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_shorts import FONT, slug  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TR = "çğıİöşüâîûÇĞÖŞÜÂÎÛ"


def glyph_ok(path):
    cmap = TTFont(path).getBestCmap()
    return [c for c in TR if ord(c) not in cmap]


def probe(p):
    d = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)]))
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next(s for s in d["streams"] if s["codec_type"] == "audio")
    return v, a, float(d["format"]["duration"])


rows = list(csv.DictReader((ROOT / "kelimeler.csv").open(encoding="utf-8")))
lines = ["# Shorts kontrol raporu", "",
         "| id | kelime | ses | görsel | dosya | çözünürlük | fps | süre (sn) | kodek | altyazı | sonuç |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
missing = {k: glyph_ok(v) for k, v in FONT.items()}
bad = 0
for r in rows:
    nn = r["id"]
    fn = f"{nn}_{slug(r['kelime'])}.mp4"
    au, im, sh = ROOT / "audio" / f"{nn}.mp3", ROOT / "images" / f"{nn}.png", ROOT / "shorts" / fn
    ok = au.exists() and im.exists() and sh.exists()
    res = fps = dur = codec = "—"
    subs = "—"
    if sh.exists():
        v, a, dur = probe(sh)
        res = f"{v['width']}×{v['height']}"
        fps = v["r_frame_rate"]
        codec = f"{v['codec_name']}+{a['codec_name']}"
        meta = json.loads(au.with_suffix(".json").read_text(encoding="utf-8"))
        segs = json.loads((ROOT / "work" / "shorts" / nn / "altyazi.json").read_text(encoding="utf-8"))
        joined = " ".join(s[0] for s in segs)
        subs_ok = joined == " ".join(meta["metin"].split()) and all(len(s[0].split()) <= 7 for s in segs)
        subs = f"{len(segs)} parça" + ("" if subs_ok else " HATA")
        exp = min(round(meta["sure_sn"] + 3, 2), 40)
        ok &= (res == "1080×1920" and fps == "30/1" and dur <= 40.05 and abs(dur - exp) < 0.1
               and codec == "h264+aac" and subs_ok)
        dur = f"{dur:.2f}"
    bad += not ok
    lines.append(f"| {nn} | {r['kelime']} | {'✓' if au.exists() else '✗'} | {'✓' if im.exists() else '✗'} | "
                 f"{fn} | {res} | {fps} | {dur} | {codec} | {subs} | {'geçti' if ok else 'KALDI'} |")
lines += ["", "Font glif kontrolü (ç ğ ı İ ö ş ü â î û ve büyükleri): " +
          ", ".join(f"NotoSans-{k}: {'tamam' if not m else 'eksik ' + ''.join(m)}" for k, m in missing.items()),
          "", f"Sonuç: {len(rows) - bad}/{len(rows)} geçti."]
(ROOT / "shorts" / "kontrol.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[-3:]))
sys.exit(1 if bad or any(missing.values()) else 0)
