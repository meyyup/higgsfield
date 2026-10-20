#!/usr/bin/env python3
"""Son Damla anahtar karelerini 2 aday (A/B seed) olarak paralel üretir. Var olanları atlar.
Kullanım: sd_kareler.py [kare_adı ...]"""
import json, pathlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from prompts_sd import KARELER
ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = {"damla": "assets/gorseller/sd_damla_ref.png", "orman": "assets/gorseller/sd_orman_ref.png"}
PARAMS = json.dumps({"resolution": "2k", "aspect_ratio": "16:9"})

def is_(ad, aday, seed):
    out = f"out/adaylar/{ad}_{aday}.png"
    if (ROOT / out).exists():
        return f"{out}: zaten var"
    model = "alibaba/qwen-image-3/edit" if KARELER[ad][0] else "alibaba/qwen-image-3/text-to-image"
    cmd = ["python3", "scripts/generate.py", "--name", ad, "--model", model,
           "--params", PARAMS, "--seed", str(seed), "--out", out]
    for r in KARELER[ad][0]:
        cmd += ["--ref", f"image_urls={REF[r]}"]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return (p.stdout + p.stderr).strip().splitlines()[-1]

adlar = sys.argv[1:] or list(KARELER)
isler = [(a, x, s) for a in adlar for x, s in (("A", 1101), ("B", 2202))]
with ThreadPoolExecutor(8) as ex:
    for sonuc in ex.map(lambda t: is_(*t), isler):
        print(sonuc, flush=True)
