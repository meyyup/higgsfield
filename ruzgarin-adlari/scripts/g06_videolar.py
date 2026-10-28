"""G6 — Her madde için 1080×1920, 30 fps, H.264 + AAC dikey video.

Girdi : media/images/NN.jpg (el çizimi fotoğrafı), media/audio/NN.m4a (öğrencinin sesi)
Çıktı : videos/NN_slug.mp4
Kullanım: python3 scripts/g06_videolar.py [--sadece 06 07 ...]

Eksik görsel ya da ses varsa madde atlanır ve raporlanır. Müzik yoktur.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageOps  # noqa: E402

from common import (ALT_BASLIK, MEDIA, PROJE_ADI, VIDEOS, maddeleri_oku,  # noqa: E402
                    pil_font)

W, H, FPS = 1080, 1920, 30
SES_BASI = 0.5          # ses videonun 0,5. saniyesinde başlar
EK_SURE = 1.5           # süre = ses + 1,5 sn
MIN_SURE, MAX_SURE = 8.0, 25.0
ZOOM = 0.08             # 1,00 -> 1,08
HEDEF_LUFS = -16
KELIME_SINIRI = 7


def calistir(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Komut başarısız: {' '.join(cmd[:6])} …\n{p.stderr[-1500:]}")
    return p


def sure_olc(yol):
    p = calistir(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=nw=1:nk=1", yol])
    return float(p.stdout.strip())


def bul(klasor, id_, uzantilar):
    for u in uzantilar:
        y = os.path.join(klasor, id_ + u)
        if os.path.exists(y):
            return y
    return None


# --- Ses ------------------------------------------------------------------------
def ses_hazirla(girdi, cikti):
    """Baştaki/sondaki sessizliği kırp, ~-16 LUFS'a iki geçişte normalize et."""
    kirp = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,"
            "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,"
            "areverse")
    olcum = calistir(["ffmpeg", "-hide_banner", "-nostats", "-i", girdi, "-af",
                      f"{kirp},loudnorm=I={HEDEF_LUFS}:TP=-1.5:LRA=11:print_format=json",
                      "-f", "null", "-"]).stderr
    m = json.loads(re.findall(r"\{[^{}]*\}", olcum)[-1])
    ln = (f"loudnorm=I={HEDEF_LUFS}:TP=-1.5:LRA=11:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    calistir(["ffmpeg", "-y", "-hide_banner", "-i", girdi, "-af", f"{kirp},{ln}",
              "-ar", "48000", "-ac", "2", cikti])
    return sure_olc(cikti)


# --- Görseller -------------------------------------------------------------------
def arka_plan(girdi, cikti):
    """Görseli ekrana sığdır (kırpmadan); boşlukları bulanık kopyasıyla doldur. 2x çözünürlük."""
    S = 2
    img = ImageOps.exif_transpose(Image.open(girdi)).convert("RGB")
    zemin = ImageOps.fit(img, (W * S, H * S), Image.LANCZOS)
    zemin = zemin.filter(ImageFilter.GaussianBlur(60)).point(lambda v: int(v * 0.55))
    on = ImageOps.contain(img, (W * S, H * S), Image.LANCZOS)
    zemin.paste(on, ((W * S - on.width) // 2, (H * S - on.height) // 2))
    zemin.save(cikti)


def metin_sar(draw, metin, font, genislik):
    satirlar, mevcut = [], ""
    for k in metin.split():
        aday = f"{mevcut} {k}".strip()
        if draw.textlength(aday, font=font) <= genislik or not mevcut:
            mevcut = aday
        else:
            satirlar.append(mevcut)
            mevcut = k
    return satirlar + ([mevcut] if mevcut else [])


def yazi_karti(metin, cikti, merkez_y, en_buyuk, en_kucuk, kalin=True, en_cok_satir=3,
               serit_alfa=150, tam_ekran_alfa=0):
    """Şeffaf 1080×1920 PNG: ortalanmış, okunaklı yarı saydam şerit üstünde beyaz yazı."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, tam_ekran_alfa))
    d = ImageDraw.Draw(img)
    for boyut in range(en_buyuk, en_kucuk - 1, -4):
        font = pil_font(boyut, kalin)
        satirlar = metin_sar(d, metin, font, W - 160)
        if len(satirlar) <= en_cok_satir:
            break
    satir_y = int(boyut * 1.25)
    toplam = satir_y * len(satirlar)
    ust = merkez_y - toplam // 2
    gen = max(d.textlength(s, font=font) for s in satirlar)
    if serit_alfa:
        d.rounded_rectangle([(W - gen) / 2 - 40, ust - 28, (W + gen) / 2 + 40, ust + toplam + 22],
                            radius=28, fill=(0, 0, 0, serit_alfa))
    for i, s in enumerate(satirlar):
        y = ust + i * satir_y
        d.text((W / 2 + 3, y + 3), s, font=font, fill=(0, 0, 0, 180), anchor="ma")
        d.text((W / 2, y), s, font=font, fill=(255, 255, 255, 255), anchor="ma")
    img.save(cikti)


def parcala(metin, sinir=KELIME_SINIRI):
    """Seslendirme metnini en çok `sinir` kelimelik parçalara böl; noktalamada kesmeyi tercih et."""
    kelimeler = metin.split()
    parcalar, mevcut = [], []
    for i, k in enumerate(kelimeler):
        mevcut.append(k)
        kalan = len(kelimeler) - i - 1
        noktalama = k[-1] in ".;:!?,"
        if len(mevcut) == sinir or (noktalama and len(mevcut) >= 3 and kalan != 1) or \
                (k[-1] in ".;:!?" and len(mevcut) >= 1):
            parcalar.append(" ".join(mevcut))
            mevcut = []
    if mevcut:
        parcalar.append(" ".join(mevcut))
    return parcalar


def zamanla(parcalar, bas, sure):
    """Parçaları ses süresine dağıt (uzunluklarıyla orantılı)."""
    agirlik = [len(p) + 8 for p in parcalar]
    toplam = sum(agirlik)
    t, out = bas, []
    for p, a in zip(parcalar, agirlik):
        d = sure * a / toplam
        out.append((p, t, t + d))
        t += d
    return out


# --- Video -----------------------------------------------------------------------
def video_uret(r, gorsel, ses, cikti, gecici):
    ses_wav = os.path.join(gecici, "ses.wav")
    ses_sure = ses_hazirla(ses, ses_wav)
    sure = min(MAX_SURE, max(MIN_SURE, ses_sure + EK_SURE))
    uyari = []
    if ses_sure + SES_BASI > sure - 0.2:
        uyari.append(f"ses {ses_sure:.1f} sn; {MAX_SURE:.0f} sn sınırına göre kısaltıldı")

    zemin = os.path.join(gecici, "zemin.png")
    arka_plan(gorsel, zemin)

    katmanlar = []  # (png, bas, bitis)
    baslik = os.path.join(gecici, "baslik.png")
    yazi_karti(r["madde"], baslik, 260, 140, 64, en_cok_satir=3, serit_alfa=120)
    katmanlar.append((baslik, 0, 3.0))
    for i, (p, a, b) in enumerate(zamanla(parcala(r["seslendirme"]), SES_BASI,
                                          min(ses_sure, sure - SES_BASI))):
        yol = os.path.join(gecici, f"alt_{i:02d}.png")
        yazi_karti(p, yol, 1480, 66, 46, kalin=True, en_cok_satir=2, serit_alfa=165)
        katmanlar.append((yol, a, min(b, sure - 1.0)))
    son = os.path.join(gecici, "son.png")
    yazi_karti(f"{PROJE_ADI} · {ALT_BASLIK}", son, H // 2, 72, 40, en_cok_satir=1, serit_alfa=0,
               tam_ekran_alfa=200)
    katmanlar.append((son, sure - 1.0, sure + 1))

    n = int(round(sure * FPS))
    girdiler = ["-framerate", str(FPS), "-loop", "1", "-i", zemin, "-i", ses_wav]
    for png, *_ in katmanlar:
        girdiler += ["-i", png]
    filtre = [f"[0:v]zoompan=z='1+{ZOOM}*on/{max(n - 1, 1)}':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}[v0]"]
    onceki = "v0"
    for i, (_, a, b) in enumerate(katmanlar):
        filtre.append(f"[{onceki}][{i + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{i + 1}]")
        onceki = f"v{i + 1}"
    filtre.append(f"[1:a]adelay={int(SES_BASI * 1000)}:all=1,apad[a]")
    calistir(["ffmpeg", "-y", "-hide_banner", *girdiler, "-filter_complex", ";".join(filtre),
              "-map", f"[{onceki}]", "-map", "[a]", "-t", f"{sure:.3f}", "-r", str(FPS),
              "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
              "-movflags", "+faststart", cikti])
    return ses_sure, sure_olc(cikti), uyari


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sadece", nargs="*", help="yalnızca bu ID'ler (ör. 06 07)")
    a = ap.parse_args()
    rows = maddeleri_oku()
    if a.sadece:
        rows = [r for r in rows if r["id"] in {s.zfill(2) for s in a.sadece}]
    os.makedirs(VIDEOS, exist_ok=True)
    rapor, atlanan = [], []
    for r in rows:
        gorsel = bul(os.path.join(MEDIA, "images"), r["id"], [".jpg", ".jpeg", ".JPG", ".png"])
        ses = bul(os.path.join(MEDIA, "audio"), r["id"], [".m4a", ".M4A", ".mp3", ".wav"])
        eksik = [ad for ad, y in (("görsel", gorsel), ("ses", ses)) if not y]
        if eksik:
            atlanan.append(f"{r['id']} {r['madde']}: eksik {', '.join(eksik)}")
            continue
        cikti = os.path.join(VIDEOS, f"{r['slug']}.mp4")
        with tempfile.TemporaryDirectory() as g:
            try:
                ses_sure, vid_sure, uyari = video_uret(r, gorsel, ses, cikti, g)
            except Exception as e:  # noqa: BLE001
                atlanan.append(f"{r['id']} {r['madde']}: HATA {e}")
                continue
        durum = "tamam" if MIN_SURE - 0.05 <= vid_sure <= MAX_SURE + 0.05 else "SÜRE DIŞI"
        satir = f"{r['id']} {os.path.basename(cikti)}: ses {ses_sure:.1f} sn, video {vid_sure:.1f} sn ({durum})"
        if uyari:
            satir += " — " + "; ".join(uyari)
        rapor.append(satir)
        print(satir, flush=True)

    ozet = [f"Üretilen: {len(rapor)}", *rapor, "", f"Atlanan: {len(atlanan)}", *atlanan]
    with open(os.path.join(VIDEOS, "rapor_g06.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ozet) + "\n")
    print(f"\nÜretilen {len(rapor)}, atlanan {len(atlanan)}")
    for s in atlanan:
        print("  ATLANDI " + s)


if __name__ == "__main__":
    main()
