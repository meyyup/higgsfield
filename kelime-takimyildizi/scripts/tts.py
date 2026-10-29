#!/usr/bin/env python3
"""G1 — ElevenLabs seslendirme: audio/NN.mp3 + audio/NN.json (karakter zaman damgaları).

Kelime ayrı ve biraz yavaş okunur, ardından kısa sessizlik, sonra cümlenin geri kalanı.
İki parça birleştirilir; zaman damgaları tek bir zaman çizelgesine kaydırılır.

  python3 scripts/tts.py 01 05 06 17 26     # yalnızca bu id'ler
  python3 scripts/tts.py --all               # 30'unun hepsi (var olanları atlar)
"""
import argparse
import base64
import csv
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_multilingual_v2"          # /v1/models: Türkçe destekli, zaman damgası destekli
VOICE_ID = "5nr6ATQepuidiLb6OT3B"         # Ozan Karaca - Rich, Warm and Calm (ses kütüphanesi, klon değil)
SETTINGS = {"stability": 0.55, "similarity_boost": 0.75, "style": 0.15, "use_speaker_boost": True}
WORD_SPEED, REST_SPEED = 0.82, 0.95
PAUSE = 0.6                                # kelimeden sonra sessizlik (sn)
SR = 44100


def rows():
    with (ROOT / "kelimeler.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tts(text, speed, prev=None, nxt=None):
    body = {"text": text, "model_id": MODEL, "language_code": "tr",
            "voice_settings": {**SETTINGS, "speed": speed}}
    if prev:
        body["previous_text"] = prev
    if nxt:
        body["next_text"] = nxt
    req = urllib.request.Request(
        f"{API}/text-to-speech/{VOICE_ID}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            sys.exit(f"HTTP {e.code}: {msg}")


def dur(p):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def make(row):
    nn, word = row["id"], row["kelime"]
    text = row["seslendirme"]
    assert text.startswith(word + "."), (nn, text)
    rest = text[len(word) + 1:].strip()
    work = ROOT / "work" / "tts"
    work.mkdir(parents=True, exist_ok=True)

    a = tts(word + ".", WORD_SPEED, nxt=rest)
    b = tts(rest, REST_SPEED, prev=word + ".")
    pa, pb = work / f"{nn}_a.mp3", work / f"{nn}_b.mp3"
    pa.write_bytes(base64.b64decode(a["audio_base64"]))
    pb.write_bytes(base64.b64decode(b["audio_base64"]))
    da = dur(pa)

    out = ROOT / "audio" / f"{nn}.mp3"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(pa), "-i", str(pb),
           "-filter_complex",
           f"[0:a]aresample={SR},apad=pad_dur={PAUSE}[a];[1:a]aresample={SR}[b];[a][b]concat=n=2:v=0:a=1[o]",
           "-map", "[o]", "-c:a", "libmp3lame", "-b:a", "128k", str(out)]
    subprocess.run(cmd, check=True)

    # karakter zaman damgalarını birleştir
    off = da + PAUSE
    al, bl = a["alignment"], b["alignment"]
    chars = al["characters"] + [" "] + bl["characters"]
    starts = al["character_start_times_seconds"] + [da] + [t + off for t in bl["character_start_times_seconds"]]
    ends = al["character_end_times_seconds"] + [off] + [t + off for t in bl["character_end_times_seconds"]]
    meta = {
        "id": nn, "kelime": word, "metin": text, "model": MODEL, "voice_id": VOICE_ID,
        "voice_settings": SETTINGS, "speed": {"kelime": WORD_SPEED, "cumle": REST_SPEED},
        "duraklama_sn": PAUSE, "sure_sn": round(dur(out), 3),
        "uretim": dt.datetime.now().isoformat(timespec="seconds"),
        "alignment": {"characters": chars, "start": starts, "end": ends},
    }
    (ROOT / "audio" / f"{nn}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    with (ROOT / "logs" / "tts.log").open("a", encoding="utf-8") as f:
        f.write(f"{meta['uretim']} {nn} {word} model={MODEL} voice={VOICE_ID} sure={meta['sure_sn']}\n")
    print(f"{nn} {word}: {meta['sure_sn']} sn", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "audio").mkdir(exist_ok=True)
    for r in rows():
        if not a.all and r["id"] not in a.ids:
            continue
        if (ROOT / "audio" / f"{r['id']}.mp3").exists() and not a.force:
            print(f"{r['id']}: var, atlandı")
            continue
        make(r)


if __name__ == "__main__":
    main()
