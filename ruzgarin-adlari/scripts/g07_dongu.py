"""G7 — videos/tum_videolar_dongu.mp4: fiziksel sıraya göre bütün videolar.

Sıra: taban (01–11), arka üst (12–21), arka alt (22–27), sol (28–32), sağ (33–39);
her bölümden önce 2 saniyelik başlık kartı. Eksik videolar atlanır ve raporlanır.
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402

from common import PROJE_ADI, VIDEOS, maddeleri_oku, pil_font  # noqa: E402
from g06_videolar import FPS, H, W, calistir, sure_olc  # noqa: E402

BOLUMLER = [
    ("Taban", "Rüzgâr gülü", lambda k: k.startswith("TABAN")),
    ("Arka duvar", "Rüzgârın adları", lambda k: k == "ARKA-UST"),
    ("Arka duvar", "Dilimizde rüzgâr", lambda k: k == "ARKA-ALT"),
    ("Sol duvar", "1000 yıl önce", lambda k: k == "SOL"),
    ("Sağ duvar", "Rüzgâr ve zanaat", lambda k: k == "SAG"),
]
BASLIK_SURE = 2.0
CIKTI = os.path.join(VIDEOS, "tum_videolar_dongu.mp4")


def baslik_karti(ust, ana, png):
    img = Image.new("RGB", (W, H), (28, 42, 58))
    d = ImageDraw.Draw(img)
    d.text((W / 2, 760), ust.upper(), font=pil_font(56), fill=(190, 205, 220), anchor="mm")
    d.text((W / 2, 900), ana, font=pil_font(104, True), fill=(255, 255, 255), anchor="mm")
    d.line([(W / 2 - 160, 1010), (W / 2 + 160, 1010)], fill=(190, 205, 220), width=4)
    d.text((W / 2, 1720), PROJE_ADI, font=pil_font(44), fill=(150, 165, 180), anchor="mm")
    img.save(png)


def main():
    rows = maddeleri_oku()
    eksik, parcalar = [], []
    with tempfile.TemporaryDirectory() as g:
        for i, (ust, ana, sec) in enumerate(BOLUMLER):
            videolar = []
            for r in rows:
                if sec(r["konum"]):
                    v = os.path.join(VIDEOS, f"{r['slug']}.mp4")
                    (videolar.append(v) if os.path.exists(v) else eksik.append(f"{r['id']} {r['madde']}"))
            if not videolar:
                continue
            png, mp4 = os.path.join(g, f"b{i}.png"), os.path.join(g, f"b{i}.mp4")
            baslik_karti(ust, ana, png)
            calistir(["ffmpeg", "-y", "-hide_banner", "-framerate", str(FPS), "-loop", "1", "-i", png,
                      "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(BASLIK_SURE),
                      "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                      "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                      "-ac", "2", mp4])
            parcalar += [mp4, *videolar]
        if not parcalar:
            raise SystemExit("Hiç video yok; önce G6'yı çalıştırın.")
        liste = os.path.join(g, "liste.txt")
        with open(liste, "w", encoding="utf-8") as f:
            for p in parcalar:
                f.write("file '" + p.replace("'", "'\\''") + "'\n")
        # Aynı parametrelerle kodlandıkları için yeniden kodlamadan birleştirilir.
        calistir(["ffmpeg", "-y", "-hide_banner", "-f", "concat", "-safe", "0", "-i", liste,
                  "-c", "copy", "-movflags", "+faststart", CIKTI])
    sure = sure_olc(CIKTI)
    print(f"{os.path.relpath(CIKTI)}: {len(parcalar)} parça, {sure / 60:.1f} dk")
    if eksik:
        print(f"Eksik ({len(eksik)}), döngüye alınmadı: " + ", ".join(eksik))
    subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height",
                    "-of", "compact", CIKTI])


if __name__ == "__main__":
    main()
