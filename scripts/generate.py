#!/usr/bin/env python3
"""Higgsfield API üretim aracı (±1°C).

Kullanım:
  generate.py image <ad> [--ref <görsel_adı> ...] [--n 2]
  generate.py video <ad> --start <görsel_adı> [--end <görsel_adı>] --duration <sn> [--n 1]
  generate.py estimate image|video ...   (aynı argümanlar, kredi tahmini; üretim yapmaz)

Prompt: prompts/<ad>.txt birebir gönderilir.
Referans görseller: assets/gorseller/<ad>.png (seçilmiş görseller).
Çıktı: out/adaylar/<ad>_aN.<ext>; log: out/uretim_logu/<ad>_aN.json; komutlar: out/komutlar.log.
Kimlik: HIGGSFIELD_API_KEY ("key_id:secret"), hiçbir yere yazılmaz.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.higgsfield.ai"
IMAGE_MODEL = "xai/grok-imagine-image-2.0"
VIDEO_MODEL = "bytedance/seedance-2.0/image-to-video"
UA = "talentcup-bir-derece/1.0"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log_cmd(line):
    with open(ROOT / "out" / "komutlar.log", "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {line}\n")


def call(method, url, body=None, auth=True, headers=None, data=None, timeout=60):
    h = {"User-Agent": UA}
    if auth:
        h["Authorization"] = "Key " + os.environ["HIGGSFIELD_API_KEY"]
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return json.loads(raw) if raw and auth else raw
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"HTTP {e.code} {method} {url}: {e.read()[:500].decode(errors='replace')}")
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            raise


def upload(path):
    """Yerel dosyayı Higgsfield depolamasına yükler, public_url döner."""
    ctype = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}[path.suffix[1:].lower()]
    r = call("POST", f"{API}/files/generate-upload-url", {"content_type": ctype})
    call("PUT", r["upload_url"], auth=False, headers=r.get("upload_headers", {}), data=path.read_bytes(), timeout=300)
    log_cmd(f"UPLOAD {path.relative_to(ROOT)} -> {r['public_url']}")
    return r["public_url"]


def ref_path(name):
    for ext in ("png", "jpg", "webp"):
        p = ROOT / "assets" / "gorseller" / f"{name}.{ext}"
        if p.exists():
            return p
    raise SystemExit(f"Referans bulunamadı: assets/gorseller/{name}.*")


def build(args, prompt, urls=None):
    if args.kind == "image":
        body = {"prompt": prompt, "quality": "medium", "resolution": "2k", "aspect_ratio": "16:9"}
        if urls:
            body["image_urls"] = urls
        return IMAGE_MODEL, body
    body = {"prompt": prompt, "duration": args.duration, "resolution": "720p", "generate_audio": False}
    if urls:
        body["image_url"] = urls[0]
        if len(urls) > 1:
            body["end_image_url"] = urls[1]
    return VIDEO_MODEL, body


def wait(status_url, timeout_s):
    t0 = time.time()
    delay = 3
    while True:
        s = call("GET", status_url)
        if s["status"] in ("completed", "failed", "nsfw", "canceled"):
            return s
        if time.time() - t0 > timeout_s:
            raise SystemExit(f"Zaman aşımı: {status_url}")
        time.sleep(delay)
        delay = min(delay * 1.5, 15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["image", "video", "estimate"])
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    first = ap.parse_args()
    sub = argparse.ArgumentParser()
    if first.mode == "estimate":
        sub.add_argument("kind", choices=["image", "video"])
    sub.add_argument("name")
    sub.add_argument("--ref", action="append", default=[])
    sub.add_argument("--start")
    sub.add_argument("--end")
    sub.add_argument("--duration", type=int, default=5)
    sub.add_argument("--n", type=int, default=None)
    sub.add_argument("--tag", default="a", help="aday dosya öneki (a1, a2 ...; yeniden üretimde r)")
    args = sub.parse_args(first.rest)
    if first.mode != "estimate":
        args.kind = first.mode
    n = args.n or (2 if args.kind == "image" else 1)

    prompt = (ROOT / "prompts" / f"{args.name}.txt").read_text(encoding="utf-8").strip()
    refs = args.ref if args.kind == "image" else [x for x in (args.start, args.end) if x]

    if first.mode == "estimate":
        model, body = build(args, prompt, ["https://example.com/ref.png"] * len(refs))
        print(json.dumps(call("POST", f"{API}/estimate/{model}", body), ensure_ascii=False))
        return

    ref_files = [ref_path(r) for r in refs]
    urls = [upload(p) for p in ref_files]
    model, body = build(args, prompt, urls)
    outdir = ROOT / "out" / "adaylar"
    logdir = ROOT / "out" / "uretim_logu"
    outdir.mkdir(parents=True, exist_ok=True)
    logdir.mkdir(parents=True, exist_ok=True)

    # Tüm adayları önce gönder (paralel), sonra bekle.
    jobs = []
    for i in range(1, n + 1):
        tag = f"{args.tag}{i}"
        while (logdir / f"{args.name}_{tag}.json").exists():
            i += n
            tag = f"{args.tag}{i}"
        sub_r = call("POST", f"{API}/{model}", body)
        log_cmd(f"POST {API}/{model} name={args.name}_{tag} body={json.dumps(body, ensure_ascii=False)} -> {sub_r.get('request_id')}")
        jobs.append((tag, sub_r, now()))
        print(f"gönderildi {args.name}_{tag}: {sub_r.get('request_id')}", flush=True)

    for tag, sub_r, t_sub in jobs:
        s = wait(sub_r["status_url"], 1800 if args.kind == "video" else 600)
        rec = {
            "zaman_gonderim": t_sub,
            "zaman_bitis": now(),
            "tur": "görsel" if args.kind == "image" else "video",
            "model": model,
            "endpoint": f"{API}/{model}",
            "prompt": prompt,
            "prompt_dosyasi": f"prompts/{args.name}.txt",
            "parametreler": {k: v for k, v in body.items() if k != "prompt"},
            "referanslar": [str(p.relative_to(ROOT)) for p in ref_files],
            "request_id": sub_r.get("request_id"),
            "durum": s["status"],
            "yanit": s,
        }
        if s["status"] == "completed":
            url = s["images"][0]["url"] if args.kind == "image" else s["video"]["url"]
            ext = Path(url.split("?")[0]).suffix or (".png" if args.kind == "image" else ".mp4")
            dest = outdir / f"{args.name}_{tag}{ext}"
            dest.write_bytes(call("GET", url, auth=False, timeout=600))
            log_cmd(f"DOWNLOAD {url} -> {dest.relative_to(ROOT)}")
            rec["sonuc_url"] = url
            rec["kaydedilen_dosya"] = str(dest.relative_to(ROOT))
            print(f"tamam {dest.relative_to(ROOT)}", flush=True)
        else:
            print(f"BAŞARISIZ {args.name}_{tag}: {s['status']} {s.get('error', '')}", flush=True)
        (logdir / f"{args.name}_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
