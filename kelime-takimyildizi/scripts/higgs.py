#!/usr/bin/env python3
"""Higgsfield: görsel düzenleme ve görselden video (giriş videosu için).

  python3 scripts/higgs.py edit  <girdi.png> <çıktı.png> "<prompt>" [--seed N] [--aspect 9:16]
  python3 scripts/higgs.py video <başlangıç.png> <bitiş.png> <çıktı.mp4> "<prompt>" [--sure 8]

Log: logs/higgsfield/<çıktı adı>.json
"""
import argparse
import datetime as dt
import json
import mimetypes
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from images import API, ROOT, call  # noqa: E402


def upload(path):
    path = pathlib.Path(path)
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    up = call("POST", f"{API}/files/generate-upload-url", {"content_type": ctype})
    import urllib.request
    req = urllib.request.Request(up["upload_url"], data=path.read_bytes(), method="PUT", headers=up["upload_headers"])
    urllib.request.urlopen(req, timeout=300).read()
    return up["public_url"]


def run(model, params, out, prompt):
    started = dt.datetime.now().isoformat(timespec="seconds")
    sub = call("POST", f"{API}/{model}", {**params, "prompt": prompt})
    print(f"{out.name}: {sub['request_id']} kuyrukta", flush=True)
    delay, t0 = 4, time.time()
    while True:
        st = call("GET", sub["status_url"])
        if st["status"] in ("completed", "failed", "nsfw", "canceled"):
            break
        if time.time() - t0 > 1800:
            sys.exit("zaman aşımı")
        time.sleep(delay)
        delay = min(delay * 1.4, 20)
    entry = {"zaman": started, "bitis": dt.datetime.now().isoformat(timespec="seconds"), "model": model,
             "prompt": prompt, "parametreler": params, "request_id": sub["request_id"], "durum": st["status"],
             "yanit": st, "kaydedilen_dosya": None}
    if st["status"] == "completed":
        media = (st.get("images") or [None])[0] or st.get("video")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(call("GET", media["url"], auth=False))
        entry["url"] = media["url"]
        entry["kaydedilen_dosya"] = str(out.relative_to(ROOT))
    logd = ROOT / "logs" / "higgsfield"
    logd.mkdir(parents=True, exist_ok=True)
    (logd / f"{out.stem}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{out.name}: {st['status']}", flush=True)
    if st["status"] != "completed":
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["edit", "video"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--sure", type=int, default=8)
    a = ap.parse_args()
    if a.cmd == "edit":
        src, out, prompt = a.args
        params = {"resolution": "2k", "aspect_ratio": a.aspect, "image_urls": [upload(ROOT / src)]}
        if a.seed is not None:
            params["seed"] = a.seed
        run("alibaba/qwen-image-3/edit", params, ROOT / out, prompt)
    else:
        start, end, out, prompt = a.args
        params = {"duration": a.sure, "resolution": "720p", "generate_audio": False,
                  "image_url": upload(ROOT / start), "end_image_url": upload(ROOT / end)}
        run("bytedance/seedance-2.0/image-to-video", params, ROOT / out, prompt)


if __name__ == "__main__":
    main()
