#!/usr/bin/env python3
"""Son Damla montajı: klipler → 1920x1080/25fps, çapraz geçiş, yazı katmanı (PIL), ses miksajı.

Çıktı: out/TalentCup-2026_Son_Damla.mp4, out/sd_altyazi.srt. Tekrar çalıştırılabilir.
Konuşma: assets/ses/sd_s*.m4a (gerçek kayıt) varsa o, yoksa work/tts/sd_s*.mp3 (geçici sentez ses).
"""
import pathlib
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H, FPS, DUR = 1920, 1080, 25, 60.0
XF = 0.35  # çapraz geçiş süresi
CLIP = ROOT / "out" / "adaylar"
WORK = ROOT / "work" / "sd"
OUT = ROOT / "out" / "TalentCup-2026_Son_Damla.mp4"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# (klip, kırpma_başı, kırpma_uzunluğu, hedef_süre, önce_bekle, sonra_bekle)
SEGMENTLER = [
    ("sd_c01_bulut", 0, 6.04, 6.0, 0, 0),      # K1 0–6
    ("sd_c02_mercek", 0, 5.04, 5.5, 0, 0),     # K2 6–11.5
    ("sd_c03_alev", 0, 5.04, 5.5, 0, 0),       # K2 11.5–17
    ("sd_c04_yorgun", 0, 2.5, 3.0, 0, 0),      # K2 17–20 (2,5 sn sonrası damlalar kaynaşıyor: kırpıldı)
    ("sd_c05_saganak", 0, 4.04, 4.0, 0, 0),    # K3 20–24
    ("sd_c06_bulus", 0, 4.04, 4.0, 0, 0),      # K3 24–28
    ("sd_c07_toplama", 0, 5.04, 6.0, 0, 0),    # K4 28–34
    ("sd_c08_kutu", 0, 5.04, 6.0, 0, 0),       # K4 34–40
    ("sd_c09_temiz", 0, 6.04, 7.25, 2.75, 0),  # K5 40–50 (ilk kare 2,75 sn sabit)
    ("sd_c10_yaprak", 0, 5.04, 5.0, 0, 5.0),   # K6 50–60 (son kare 5 sn sabit)
]

# (dosya, başlangıç_sn, metin)
KONUSMA = [
    ("sd_s1_damla", 0.3, "Ben Damla. Arkadaşlarımla yangınları\nsöndürmekte çok zorlanıyoruz."),
    ("sd_s2_pit", 17.2, "Ne kadar yağsak da yetmiyor!"),
    ("sd_s3_damla", 22.0, "Ormana atılan cam şişeler, mercek gibi güneşi\ntopluyor ve yangın başlatabiliyor."),
    ("sd_s4_damla", 29.0, "O yüzden, yangın söndürmediğimiz zamanlarda,\ncam şişeleri geri dönüşüm kutularına atıyoruz."),
    ("sd_s5_pit", 44.5, "Bu yaz hiç yangın çıkmadı!"),
]

# (başla, bitir, metin, boyut, y_oranı) — yazı kartları
KARTLAR = [
    (3.0, 6.0, "Ben Damla.", 64, .62),
    (14.0, 20.0, "Orman yangınlarının çoğu insan kaynaklı.", 54, .66),
    (24.0, 28.0, "Bir şişe = bir büyüteç", 64, .62),
    (42.0, 50.0, "Bu yaz: 0 yangın", 72, .62),
    (54.0, 60.0, "Ateşi söndürmek zor, başlamasını önlemek kolay.", 52, .40),
    (55.5, 60.0, "Şişeni doğaya değil, geri dönüşüme at.", 52, .50),
    (57.5, 60.0, "TalentCup-2026", 40, .62),
]


def log(cmd):
    with open(ROOT / "out" / "komutlar.log", "a", encoding="utf-8") as f:
        f.write(" ".join(str(c) for c in cmd) + "\n")


def ff(*args):
    cmd = ["ffmpeg", "-v", "error", "-y", *map(str, args)]
    log(cmd)
    subprocess.run(cmd, check=True, cwd=ROOT)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]).decode())


def konusma_dosyasi(ad):
    gercek = ROOT / "assets" / "ses" / f"{ad}.m4a"
    return gercek if gercek.exists() else ROOT / "work" / "tts" / f"{ad}.mp3"


def segmentler():
    WORK.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, (ad, ss, ln, hedef, once, sonra) in enumerate(SEGMENTLER):
        uzat = XF if i < len(SEGMENTLER) - 1 else 0
        toplam = once + hedef + sonra + uzat
        vf = (f"trim=start={ss}:duration={ln},setpts=PTS-STARTPTS,setpts=PTS*{hedef / ln:.5f},"
              f"scale={W}:{H}:flags=lanczos,fps={FPS}")
        if once:
            vf += f",tpad=start_mode=clone:start_duration={once}"
        vf += f",tpad=stop_mode=clone:stop_duration={sonra + uzat + 0.2}"
        vf += f",setpts=N/{FPS}/TB"  # tpad sonrası zaman damgalarını sıralı yap (kare düşmesin)
        out = WORK / f"{i:02d}_{ad}.mp4"
        ff("-i", CLIP / f"{ad}.mp4", "-vf", vf, "-frames:v", round(toplam * FPS), "-an",
           "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", out)
        paths.append((out, once + hedef + sonra))
    return paths


def birlestir(paths):
    args, fc = [], []
    for p, _ in paths:
        args += ["-i", p]
    prev, t = "[0:v]", 0.0
    for i in range(1, len(paths)):
        t += paths[i - 1][1]
        lab = f"[x{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={t:.3f}{lab}")
        prev = lab
    out = WORK / "video.mp4"
    ff(*args, "-filter_complex", ";".join(fc), "-map", prev, "-t", DUR, "-c:v", "libx264", "-crf", "14",
       "-preset", "medium", "-pix_fmt", "yuv420p", out)
    return out


def metin(d, xy, s, font, fill=(255, 255, 255, 255), anchor="mm"):
    d.multiline_text(xy, s, font=font, fill=fill, anchor=anchor, align="center", spacing=10)


def golgeli(katman, xy, s, font, alpha, anchor="mm"):
    g = Image.new("RGBA", katman.size, (0, 0, 0, 0))
    metin(ImageDraw.Draw(g), (xy[0] + 3, xy[1] + 3), s, font, (0, 0, 0, int(200 * alpha)), anchor)
    g = g.filter(ImageFilter.GaussianBlur(4))
    katman.alpha_composite(g)
    metin(ImageDraw.Draw(katman), xy, s, font, (255, 255, 255, int(255 * alpha)), anchor)


def fade(t, a, b, f=0.3):
    if t < a or t > b:
        return 0.0
    return max(0.0, min(1.0, (t - a) / f, (b - t) / f if b < DUR else 1.0))


def katman_video():
    """PIL ile şeffaf yazı katmanını kare kare üretip qtrle .mov olarak yazar."""
    fonts = {}

    def F(sz, bold=True):
        k = (sz, bold)
        if k not in fonts:
            fonts[k] = ImageFont.truetype(FONT_B if bold else FONT, sz)
        return fonts[k]

    altyazi = [(s, s + dur(konusma_dosyasi(ad)), m) for ad, s, m in KONUSMA]
    out = WORK / "katman.mov"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "qtrle", str(out)]
    log(cmd[:-1] + ["(PIL kareleri)", str(out)])
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, cwd=ROOT)
    bos = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    onceki_anahtar, onceki_bayt = None, None
    for n in range(int(DUR * FPS)):
        t = n / FPS
        ogeler = []
        a = fade(t, 0.2, 3.0)
        if a:
            ogeler.append(("baslik", round(a, 2)))
        for i, (s, e, *_r) in enumerate(KARTLAR):
            a = fade(t, s, e)
            if a:
                ogeler.append(("kart", i, round(a, 2)))
        for i, (s, e, _m) in enumerate(altyazi):
            a = fade(t, s, e + 0.2, 0.15)
            if a:
                ogeler.append(("alt", i, round(a, 2)))
        if 28.0 <= t < 40.0:
            ogeler.append(("sayac", 1 + int((t - 28.0) / 12.0 * 47), round(fade(t, 28, 40), 2)))
        anahtar = tuple(ogeler)
        if anahtar != onceki_anahtar:
            im = bos.copy()
            for o in ogeler:
                if o[0] == "baslik":
                    golgeli(im, (W / 2, H * .42), "SON DAMLA", F(150), o[1])
                    golgeli(im, (W / 2, H * .56), "bir yağmur damlasının hikâyesi", F(44, False), o[1])
                elif o[0] == "kart":
                    s, e, m, sz, y = KARTLAR[o[1]]
                    golgeli(im, (W / 2, H * y), m, F(sz), o[2])
                elif o[0] == "alt":
                    golgeli(im, (W / 2, H * .88), altyazi[o[1]][2], F(40, False), o[2])
                elif o[0] == "sayac":
                    golgeli(im, (W - 60, 60), f"Toplanan şişe: {o[1]}", F(52), o[2], anchor="ra")
            onceki_anahtar, onceki_bayt = anahtar, im.tobytes()
        p.stdin.write(onceki_bayt)
    p.stdin.close()
    if p.wait():
        raise SystemExit("katman.mov yazılamadı")
    return out, altyazi


def srt(altyazi):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    satirlar = []
    for i, (s, e, m) in enumerate(altyazi, 1):
        satirlar += [str(i), f"{ts(s)} --> {ts(e)}", m, ""]
    (ROOT / "out" / "sd_altyazi.srt").write_text("\n".join(satirlar), encoding="utf-8")


def ses(altyazi):
    """Konuşma orijinal seviye; müzik konuşma altında −12 dB; efektler; ~−14 LUFS."""
    args = ["-i", ROOT / "assets/ses/sd_muzik.wav", "-i", ROOT / "assets/ses/sd_efekt.wav"]
    fc, mix = [], []
    for k, (ad, s, _m) in enumerate(KONUSMA):
        args += ["-i", konusma_dosyasi(ad)]
        ms = int(s * 1000)
        fc.append(f"[{k + 2}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[k{k}]")
        mix.append(f"[k{k}]")
    duck = "+".join(f"between(t,{s - .2:.2f},{e + .3:.2f})" for s, e, _ in altyazi)
    fc.append(f"[0:a]volume='if({duck},0.25,1)':eval=frame,volume=0.55[m]")
    fc.append("[1:a]volume=0.8[e]")
    fc.append(f"[m][e]{''.join(mix)}amix=inputs={len(mix) + 2}:normalize=0,"
              f"loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{DUR}[a]")
    out = WORK / "ses.wav"
    ff(*args, "-filter_complex", ";".join(fc), "-map", "[a]", "-ar", 48000, out)
    return out


def main():
    paths = segmentler()
    video = birlestir(paths)
    katman, altyazi = katman_video()
    srt(altyazi)
    sesdosya = ses(altyazi)
    ff("-i", video, "-i", katman, "-i", sesdosya, "-filter_complex", "[0:v][1:v]overlay=format=auto[v]",
       "-map", "[v]", "-map", "2:a", "-t", DUR, "-c:v", "libx264", "-crf", "18", "-preset", "medium",
       "-pix_fmt", "yuv420p", "-r", FPS, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT)
    print(f"{OUT.relative_to(ROOT)}: {dur(OUT):.2f} sn")


if __name__ == "__main__":
    main()
