#!/usr/bin/env python3
"""Seçilen klip ve görselleri 1920x1080 / 25 fps / sessiz hâle getirir → work/norm/.

Oran farkı merkezden kırpılır. Tekrar çalıştırılabilir; çıktı varsa ve kaynaktan yeniyse atlanır.
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
NORM = ROOT / "work" / "norm"
CMD_LOG = ROOT / "out" / "komutlar.log"
VF = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1"


def run(cmd):
    with CMD_LOG.open("a", encoding="utf-8") as f:
        f.write("ffmpeg " + " ".join(cmd[1:]) + "\n")
    subprocess.run(cmd, check=True)


def fresh(src, dst):
    return dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime


def main():
    NORM.mkdir(parents=True, exist_ok=True)
    for src in sorted((ROOT / "assets" / "videolar").glob("*.mp4")):
        dst = NORM / src.name
        if not fresh(src, dst):
            run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-an", "-vf", f"{VF},fps=25",
                 "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", str(dst)])
    for src in sorted((ROOT / "assets" / "gorseller").glob("*.png")):
        dst = NORM / src.name
        if not fresh(src, dst):
            run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", VF, str(dst)])
    print(f"normalize: {len(list(NORM.iterdir()))} dosya → {NORM.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
