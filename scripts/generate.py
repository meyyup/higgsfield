#!/usr/bin/env python3
"""Higgsfield API ile tek bir üretim: yükle → gönder → bekle → indir → logla.

Örnek:
  python3 scripts/generate.py --name kadraj_ref --model alibaba/qwen-image-3/text-to-image \
      --params '{"resolution":"2k","aspect_ratio":"16:9"}' --out out/adaylar/kadraj_ref_A.png --seed 11

  python3 scripts/generate.py --name pencere_kotu_2030 --model alibaba/qwen-image-3/edit \
      --ref image_urls=assets/gorseller/kadraj_ref.png --out ...

Prompt her zaman prompts/<name>.txt dosyasından birebir okunur.
Log: out/uretim_logu/<çıktı_dosya_adı>.json, komut: out/komutlar.log (anahtar gizlenir).
"""
import argparse
import datetime as dt
import json
import mimetypes
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.higgsfield.ai"
LOG_DIR = ROOT / "out" / "uretim_logu"
CMD_LOG = ROOT / "out" / "komutlar.log"
UPLOAD_CACHE = ROOT / "work" / "upload_cache.json"


def key():
    k = os.environ.get("HIGGSFIELD_API_KEY")
    if not k:
        sys.exit("HIGGSFIELD_API_KEY tanımlı değil")
    return k


def call(method, url, body=None, auth=True, headers=None, raw=None):
    h = dict(headers or {})
    if auth:
        h["Authorization"] = f"Key {key()}"
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = r.read()
                return json.loads(txt) if txt and r.headers.get_content_type() == "application/json" else txt
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code in (429, 502, 503, 504) and attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            sys.exit(f"HTTP {e.code} {url}: {msg}")
        except urllib.error.URLError:
            if attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            raise


def log_cmd(line):
    CMD_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CMD_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{dt.datetime.now().isoformat(timespec='seconds')}] {line}\n")


def upload(path):
    """Yerel dosyayı yükler, public_url döner. Aynı dosya tekrar yüklenmez."""
    path = pathlib.Path(path)
    cache = json.loads(UPLOAD_CACHE.read_text()) if UPLOAD_CACHE.exists() else {}
    ck = f"{path.resolve()}:{path.stat().st_mtime_ns}"
    if ck in cache:
        return cache[ck]
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    up = call("POST", f"{API}/files/generate-upload-url", {"content_type": ctype})
    call("PUT", up["upload_url"], auth=False, headers=up["upload_headers"], raw=path.read_bytes())
    log_cmd(f"UPLOAD {path.relative_to(ROOT)} -> {up['public_url']}")
    cache[ck] = up["public_url"]
    UPLOAD_CACHE.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_CACHE.write_text(json.dumps(cache, indent=1))
    return up["public_url"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="prompts/<name>.txt")
    ap.add_argument("--model", required=True)
    ap.add_argument("--params", default="{}")
    ap.add_argument("--ref", action="append", default=[],
                    help="param=yerel_dosya (image_urls için birden çok kez verilebilir)")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    prompt = (ROOT / "prompts" / f"{a.name}.txt").read_text(encoding="utf-8").strip()
    params = json.loads(a.params)
    params["prompt"] = prompt
    if a.seed is not None:
        params["seed"] = a.seed
    refs = {}
    for r in a.ref:
        p, f = r.split("=", 1)
        url = upload(ROOT / f)
        refs.setdefault(p, []).append(f)
        if p.endswith("_urls"):
            params.setdefault(p, []).append(url)
        else:
            params[p] = url

    out = ROOT / a.out
    started = dt.datetime.now().isoformat(timespec="seconds")
    log_cmd(f"POST {API}/{a.model} name={a.name} out={a.out} "
            f"params={json.dumps({k: v for k, v in params.items() if k != 'prompt'}, ensure_ascii=False)}")
    sub = call("POST", f"{API}/{a.model}", params, headers={"Idempotency-Key": str(uuid.uuid4())})
    rid = sub["request_id"]
    print(f"{a.out}: {rid} queued", flush=True)

    delay, t0 = 3, time.time()
    while True:
        st = call("GET", sub["status_url"])
        if st["status"] in ("completed", "failed", "nsfw", "canceled"):
            break
        if time.time() - t0 > 1800:
            sys.exit(f"zaman aşımı: {rid}")
        time.sleep(delay)
        delay = min(delay * 1.5, 20)

    entry = {
        "zaman": started, "bitis": dt.datetime.now().isoformat(timespec="seconds"),
        "model": a.model, "prompt": prompt, "prompt_dosyasi": f"prompts/{a.name}.txt",
        "parametreler": {k: v for k, v in params.items() if k != "prompt"},
        "referans_dosyalar": refs, "request_id": rid, "durum": st["status"],
        "yanit": st, "kaydedilen_dosya": None,
    }
    if st["status"] == "completed":
        media = (st.get("images") or [None])[0] or st.get("video")
        entry["url"] = media["url"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(call("GET", media["url"], auth=False))
        entry["kaydedilen_dosya"] = str(out.relative_to(ROOT))
        log_cmd(f"DOWNLOAD {media['url']} -> {a.out}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / f"{out.stem}.json").write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{a.out}: {st['status']}", flush=True)
    if st["status"] != "completed":
        sys.exit(1)


if __name__ == "__main__":
    main()
