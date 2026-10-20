#!/usr/bin/env python3
"""Son Damla kliplerini Seedance 2.0 ile paralel üretir. Var olanları atlar.
Kullanım: sd_klipler.py [klip_adı ...]"""
import json, pathlib, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from prompts_sd import KLIPLER
ROOT = pathlib.Path(__file__).resolve().parent.parent

def is_(ad):
    bas, son, sure, _ = KLIPLER[ad]
    out = f"out/adaylar/{ad}.mp4"
    if (ROOT / out).exists():
        return f"{out}: zaten var"
    params = json.dumps({"duration": sure, "resolution": "720p", "generate_audio": False})
    cmd = ["python3", "scripts/generate.py", "--name", ad, "--model", "bytedance/seedance-2.0/image-to-video",
           "--params", params, "--out", out, "--ref", f"image_url=assets/gorseller/{bas}.png"]
    if son:
        cmd += ["--ref", f"end_image_url=assets/gorseller/{son}.png"]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return (p.stdout + p.stderr).strip().splitlines()[-1]

with ThreadPoolExecutor(5) as ex:
    for sonuc in ex.map(is_, sys.argv[1:] or list(KLIPLER)):
        print(sonuc, flush=True)
