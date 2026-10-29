#!/usr/bin/env python3
"""G2 — Higgsfield görsel üretimi: images/NN.png (9:16), prompt kelimeler.csv'den birebir.

  python3 scripts/images.py 01 11 21          # yalnızca bu id'ler
  python3 scripts/images.py --all             # hepsi (var olanları atlar)
  python3 scripts/images.py 05 --force --seed 77   # metin çıkan görseli yeniden üret

Log: logs/higgsfield/NN.json (zaman, model, prompt, parametreler, request_id, URL).
"""
import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.higgsfield.ai"
MODEL = "alibaba/qwen-image-3/text-to-image"
PARAMS = {"resolution": "2k", "aspect_ratio": "9:16"}
NEG = "text, letters, words, numbers, writing, calligraphy, signature, watermark, logo, realistic human face, photo"


def call(method, url, body=None, auth=True):
    h = {}
    if auth:
        h["Authorization"] = f"Key {os.environ['HIGGSFIELD_API_KEY']}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
        h["Idempotency-Key"] = str(uuid.uuid4())
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = r.read()
                return json.loads(txt) if r.headers.get_content_type() == "application/json" else txt
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code in (429, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"HTTP {e.code} {url}: {msg}")
        except urllib.error.URLError:
            if attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            raise


def gen(row, seed, out):
    nn = row["id"]
    params = {**PARAMS, "prompt": row["higgsfield_prompt"], "negative_prompt": NEG}
    if seed is not None:
        params["seed"] = seed
    started = dt.datetime.now().isoformat(timespec="seconds")
    sub = call("POST", f"{API}/{MODEL}", params)
    rid = sub["request_id"]
    print(f"{nn}: {rid} kuyrukta", flush=True)
    delay, t0 = 3, time.time()
    while True:
        st = call("GET", sub["status_url"])
        if st["status"] in ("completed", "failed", "nsfw", "canceled"):
            break
        if time.time() - t0 > 1200:
            raise SystemExit(f"zaman aşımı {nn}")
        time.sleep(delay)
        delay = min(delay * 1.5, 15)
    entry = {"id": nn, "kelime": row["kelime"], "zaman": started,
             "bitis": dt.datetime.now().isoformat(timespec="seconds"), "model": MODEL,
             "prompt": row["higgsfield_prompt"],
             "parametreler": {k: v for k, v in params.items() if k != "prompt"},
             "request_id": rid, "durum": st["status"], "yanit": st, "kaydedilen_dosya": None}
    if st["status"] == "completed":
        url = st["images"][0]["url"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(call("GET", url, auth=False))
        entry["url"] = url
        entry["kaydedilen_dosya"] = str(out.relative_to(ROOT))
    logd = ROOT / "logs" / "higgsfield"
    logd.mkdir(parents=True, exist_ok=True)
    (logd / f"{out.stem}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{nn}: {st['status']} -> {entry['kaydedilen_dosya']}", flush=True)
    return st["status"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    with (ROOT / "kelimeler.csv").open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if a.all or r["id"] in a.ids]
    todo = []
    for r in rows:
        out = ROOT / "images" / f"{r['id']}.png"
        if out.exists() and not a.force:
            print(f"{r['id']}: var, atlandı")
            continue
        if out.exists():  # eskiyi sakla
            old = ROOT / "work" / "reddedilen" / f"{r['id']}_{int(time.time())}.png"
            old.parent.mkdir(parents=True, exist_ok=True)
            out.rename(old)
        seed = a.seed if a.seed is not None else 4200 + int(r["id"])
        todo.append((r, seed, out))
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda t: gen(*t), todo))
    if any(s != "completed" for s in res):
        sys.exit(1)


if __name__ == "__main__":
    main()
