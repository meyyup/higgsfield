#!/usr/bin/env python3
"""Son Damla seslendirmesi: ElevenLabs (ELEVENLABS_API_KEY).

  sd_elevenlabs.py tasarla          Damla ve Pıt için Voice Design ile ses adayları üretir
                                    → assets/ses/elevenlabs/aday_<karakter>_<n>.mp3 (+ adaylar.json)
  sd_elevenlabs.py sec damla=1 pit=2  seçilen adayları kalıcı ses olarak kaydeder (sesler.json)
  sd_elevenlabs.py oku              5 repliği seçilen seslerle üretir → assets/ses/elevenlabs/sd_s*.mp3

Her çağrı out/uretim_logu/elevenlabs_*.json ve out/komutlar.log'a yazılır; anahtar yazılmaz.
"""
import base64
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1"
W = ROOT / "assets" / "ses" / "elevenlabs"
LOG = ROOT / "out" / "uretim_logu"
TTS_MODEL = "eleven_multilingual_v2"

KARAKTER = {
    "damla": ("Female voice actor performing a cheerful, brave animated cartoon heroine, a tiny raindrop, in Turkish. "
              "Bright, light, high-pitched, warm and expressive, slightly breathless. Clear studio recording.",
              "Ben Damla. Arkadaşlarımla yangınları söndürmekte çok zorlanıyoruz. Ama pes etmek yok! "
              "Cam şişeleri toplayıp geri dönüşüme taşıyacağız."),
    "pit": ("Voice actor performing a tiny, excitable cartoon sidekick, a little raindrop, in Turkish. Very high, "
            "squeaky, cute and emotional, a little fast and bouncy. Clear studio recording.",
            "Ne kadar yağsak da yetmiyor! Ama bak, bu yaz hiç yangın çıkmadı! Yaşasın! "
            "Haydi Damla, bir şişe daha taşıyalım!"),
}
REPLIKLER = [
    ("sd_s1_damla", "damla", "Ben Damla. Arkadaşlarımla yangınları söndürmekte çok zorlanıyoruz."),
    ("sd_s2_pit", "pit", "Ne kadar yağsak da yetmiyor!"),
    ("sd_s3_damla", "damla", "Ormana atılan cam şişeler, mercek gibi güneşi topluyor ve yangın başlatabiliyor."),
    ("sd_s4_damla", "damla", "O yüzden, yangın söndürmediğimiz zamanlarda, cam şişeleri geri dönüşüm kutularına atıyoruz."),
    ("sd_s5_pit", "pit", "Bu yaz hiç yangın çıkmadı!"),
]


def key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        sys.exit("ELEVENLABS_API_KEY tanımlı değil (ortam ayarlarına ekleyip yeni oturum açın)")
    return k


def call(path, body, raw=False):
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key(), "Content-Type": "application/json"})
    with open(ROOT / "out" / "komutlar.log", "a", encoding="utf-8") as f:
        f.write(f"[{dt.datetime.now().isoformat(timespec='seconds')}] POST {API}{path} "
                f"{json.dumps(body, ensure_ascii=False)}\n")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {path}: {e.read()[:500].decode(errors='replace')}")
    return data if raw else json.loads(data)


def logla(ad, kayit):
    LOG.mkdir(parents=True, exist_ok=True)
    kayit["zaman"] = dt.datetime.now().isoformat(timespec="seconds")
    (LOG / f"elevenlabs_{ad}.json").write_text(json.dumps(kayit, ensure_ascii=False, indent=2), encoding="utf-8")


def tasarla():
    W.mkdir(parents=True, exist_ok=True)
    adaylar = {}
    for kr, (tarif, metin) in KARAKTER.items():
        body = {"voice_description": tarif, "text": metin}
        r = call("/text-to-voice/design", body)
        adaylar[kr] = []
        for n, p in enumerate(r.get("previews", []), 1):
            out = W / f"aday_{kr}_{n}.mp3"
            out.write_bytes(base64.b64decode(p["audio_base_64"]))
            adaylar[kr].append({"n": n, "generated_voice_id": p["generated_voice_id"], "dosya": str(out.relative_to(ROOT))})
            print(out.relative_to(ROOT))
        logla(f"tasarla_{kr}", {"endpoint": "/text-to-voice/design", "istek": body,
                                "adaylar": adaylar[kr]})
    (W / "adaylar.json").write_text(json.dumps(adaylar, ensure_ascii=False, indent=2), encoding="utf-8")


def sec(secimler):
    adaylar = json.loads((W / "adaylar.json").read_text(encoding="utf-8"))
    sesler = {}
    for s in secimler:
        kr, n = s.split("=")
        a = adaylar[kr][int(n) - 1]
        body = {"voice_name": f"Son Damla - {kr}", "voice_description": KARAKTER[kr][0],
                "generated_voice_id": a["generated_voice_id"]}
        r = call("/text-to-voice", body)
        sesler[kr] = r["voice_id"]
        logla(f"sec_{kr}", {"endpoint": "/text-to-voice", "istek": body, "voice_id": r["voice_id"]})
        print(kr, "→", r["voice_id"])
    (W / "sesler.json").write_text(json.dumps(sesler, indent=2), encoding="utf-8")


def oku():
    sesler = json.loads((W / "sesler.json").read_text(encoding="utf-8"))
    for ad, kr, metin in REPLIKLER:
        body = {"text": metin, "model_id": TTS_MODEL, "language_code": "tr",
                "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True}}
        out = W / f"{ad}.mp3"
        out.write_bytes(call(f"/text-to-speech/{sesler[kr]}?output_format=mp3_44100_128", body, raw=True))
        logla(ad, {"endpoint": f"/text-to-speech/{sesler[kr]}", "model": TTS_MODEL, "karakter": kr,
                   "istek": body, "kaydedilen_dosya": str(out.relative_to(ROOT))})
        print(out.relative_to(ROOT))


if __name__ == "__main__":
    komut = sys.argv[1] if len(sys.argv) > 1 else ""
    {"tasarla": lambda: tasarla(), "sec": lambda: sec(sys.argv[2:]), "oku": lambda: oku()}.get(
        komut, lambda: sys.exit(__doc__))()
