#!/usr/bin/env python3
"""G3 — Shorts montajı: shorts/NN_slug.mp4 (1080×1920, 30 fps, H.264 + AAC, müzik yok).

Katmanlar (PIL ile şeffaf PNG → ffmpeg overlay):
  arka plan: clips/NN.mp4 varsa o, yoksa images/NN.png yavaş yakınlaşma 1,00 → 1,08
  0–2,5 sn : koyulaştırma + ortada çok büyük kelime (sonunda yumuşak geçiş)
  sürekli  : üst bant (kategori rengi, KATEGORİ solda, NN/30 sağda)
  altyazı  : seslendirme metni ≤7 kelimelik parçalar, ElevenLabs zaman damgalarıyla
  son 2 sn : koyu zemin + "Kelime Takımyıldızı · Türkçenin Kelime Hazinesi" + YZ notu

  python3 scripts/build_shorts.py 01          # tek video
  python3 scripts/build_shorts.py --all
"""
import argparse
import csv
import json
import pathlib
import re
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
BAND = 180
INTRO, OUTRO, LEAD = 2.5, 2.0, 0.3      # ses 0,3 sn'de başlar
MAX_LEN = 40.0
FONT = {w: str(ROOT / "fonts" / f"NotoSans-{w}.ttf") for w in ("Regular", "Bold", "Black")}
END_LINE = "Kelime Takımyıldızı · Türkçenin Kelime Hazinesi"
AI_NOTE = "seslendirme ve görseller yapay zekâ ile üretilmiştir."  # küçük harflerle (brif)

ASCII = str.maketrans("çğıİöşüâîûÇĞÖŞÜÂÎÛ", "cgiiosuaiuCGOSUAIU")


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def slug(word):
    return re.sub(r"[^a-z0-9]+", "", word.translate(ASCII).lower())


def font(w, size):
    return ImageFont.truetype(FONT[w], size)


def fit(draw, text, w, size, maxw):
    while size > 10:
        f = font(w, size)
        if draw.textlength(text, font=f) <= maxw:
            return f
        size -= 2
    return font(w, size)


def shadow_text(img, xy, text, f, fill="white", anchor="mm", blur=6, alpha=170):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 4), text, font=f, fill=(0, 0, 0, alpha), anchor=anchor)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(img).text(xy, text, font=f, fill=fill, anchor=anchor)


def band_png(row, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, BAND], fill=row["renk"])
    f = fit(d, tr_upper(row["kategori"]), "Black", 64, W - 300)
    d.text((48, BAND // 2), tr_upper(row["kategori"]), font=f, fill="white", anchor="lm")
    d.text((W - 48, BAND // 2), f"{row['id']}/30", font=font("Bold", 56), fill="white", anchor="rm")
    img.save(path)


def intro_png(row, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 120))   # hafif koyulaştırma
    d = ImageDraw.Draw(img)
    f = fit(d, row["kelime"], "Black", 230, W - 120)
    shadow_text(img, (W // 2, H // 2), row["kelime"], f, blur=10, alpha=200)
    img.save(path)


def outro_png(path):
    img = Image.new("RGBA", (W, H), (18, 16, 28, 255))
    d = ImageDraw.Draw(img)
    f = fit(d, END_LINE, "Bold", 60, W - 100)
    d.text((W // 2, H // 2 - 20), END_LINE, font=f, fill="white", anchor="mm")
    d.text((W // 2, H // 2 + 60), AI_NOTE, font=font("Regular", 32), fill=(205, 200, 220), anchor="mm")
    img.save(path)


def sub_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font("Bold", 60)
    words, lines, cur = text.split(), [], ""
    for wd in words:                      # en çok 2 satır, 960 px
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) > W - 140 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    lh = 78
    cy = 1440                             # alt üçte bir
    top = cy - lh * len(lines) / 2 - 26
    bot = cy + lh * len(lines) / 2 + 26
    d.rounded_rectangle([40, top, W - 40, bot], radius=28, fill=(0, 0, 0, 150))
    for i, ln in enumerate(lines):
        d.text((W // 2, cy - lh * (len(lines) - 1) / 2 + i * lh), ln, font=f, fill="white", anchor="mm")
    img.save(path)


def chunks(text, maxw=7):
    """Cümlelere böl, uzun cümleyi en çok 7 kelimelik dengeli parçalara ayır. (başlangıç, bitiş) karakter indeksi döner."""
    out = []
    for m in re.finditer(r"[^.!?]+[.!?]*", text):
        sent = m.group()
        ws = [(w.start() + m.start(), w.end() + m.start()) for w in re.finditer(r"\S+", sent)]
        if not ws:
            continue
        n = -(-len(ws) // maxw)
        size = -(-len(ws) // n)
        for i in range(0, len(ws), size):
            grp = ws[i:i + size]
            out.append((grp[0][0], grp[-1][1]))
    return out


def subtitle_times(meta):
    text = meta["metin"]
    al = meta["alignment"]
    assert "".join(al["characters"]) == text, "zaman damgası metinle eşleşmiyor"
    segs = []
    for a, b in chunks(text):
        segs.append([text[a:b], al["start"][a] + LEAD, al["end"][b - 1] + LEAD])
    for i in range(len(segs) - 1):        # boşluk bırakma: bir sonraki parçaya kadar ekranda kalsın
        segs[i][2] = segs[i + 1][1]
    return segs


def build(row):
    nn = row["id"]
    meta = json.loads((ROOT / "audio" / f"{nn}.json").read_text(encoding="utf-8"))
    adur = meta["sure_sn"]
    T = min(round(adur + 3, 2), MAX_LEN)
    work = ROOT / "work" / "shorts" / nn
    work.mkdir(parents=True, exist_ok=True)
    band_png(row, work / "band.png")
    intro_png(row, work / "intro.png")
    outro_png(work / "outro.png")
    segs = subtitle_times(meta)
    for i, (t, _, _) in enumerate(segs):
        sub_png(t, work / f"sub{i:02d}.png")
    (work / "altyazi.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")

    clip = ROOT / "clips" / f"{nn}.mp4"
    N = int(round(T * FPS))
    if clip.exists():
        bg = ["-stream_loop", "-1", "-i", str(clip)]
        bgf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
               f"fps={FPS},setsar=1,trim=duration={T}[bg]")
    else:
        bg = ["-loop", "1", "-framerate", str(FPS), "-i", str(ROOT / "images" / f"{nn}.png")]
        bgf = (f"[0:v]scale={W*4}:{H*4}:flags=lanczos,"
               f"zoompan=z='1+0.08*on/{N}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={N}:s={W}x{H}:fps={FPS},"
               f"setsar=1,trim=duration={T}[bg]")

    inputs = bg + ["-i", str(ROOT / "audio" / f"{nn}.mp3")]
    pngs = ["band.png", "intro.png", "outro.png"] + [f"sub{i:02d}.png" for i in range(len(segs))]
    for p in pngs:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", str(T), "-i", str(work / p)]

    fc = [bgf]
    fc.append(f"[3:v]format=rgba,fade=t=out:st={INTRO - 0.4}:d=0.4:alpha=1[intro]")
    fc.append(f"[4:v]format=rgba,fade=t=in:st={T - OUTRO}:d=0.3:alpha=1[outro]")
    fc.append("[bg][intro]overlay=enable='lt(t,%s)'[i1]" % INTRO)
    cur = "i1"
    for i, (_, a, b) in enumerate(segs):
        b = min(b, T - OUTRO)
        fc.append(f"[{cur}][{5 + i}:v]overlay=enable='between(t,{a:.2f},{b:.2f})'[s{i}]")
        cur = f"s{i}"
    fc.append(f"[{cur}][outro]overlay=enable='gte(t,{T - OUTRO})'[o1]")
    fc.append("[o1][2:v]overlay,format=yuv420p[v]")
    fc.append(f"[1:a]adelay={int(LEAD*1000)}:all=1,apad,atrim=duration={T},"
              "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")

    out = ROOT / "shorts" / f"{nn}_{slug(row['kelime'])}.mp4"
    out.parent.mkdir(exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
           "-map", "[v]", "-map", "[a]", "-t", str(T), "-r", str(FPS),
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", str(out)]
    (work / "ffmpeg_cmd.txt").write_text(" ".join(cmd), encoding="utf-8")
    subprocess.run(cmd, check=True)
    print(f"{out.relative_to(ROOT)}: {T} sn, {len(segs)} altyazı parçası", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    with (ROOT / "kelimeler.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if a.all or r["id"] in a.ids:
                build(r)


if __name__ == "__main__":
    main()
