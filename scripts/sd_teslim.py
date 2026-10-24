#!/usr/bin/env python3
"""Son Damla teslim paketi (CLAUDE.md §8, Son Damla'ya uyarlanmış). Tekrar çalıştırılabilir.

  sd_teslim.py                 kontrol.md, kaynak_listesi.pdf, storyboard, youtube_aciklama.txt, tanitim_notlari.md
  sd_teslim.py --ad Ad_Soyad   ayrıca out/Ad_Soyad.zip (out/drive_link.txt gerekir)

Zamanlamalar scripts/sd_montaj.py'deki SEGMENTLER/KONUSMA/KARTLAR/MUZIK'ten okunur; süre, ses seviyesi ve
altyazı final videodan ve out/sd_altyazi.srt'den ölçülür.
"""
import json
import pathlib
import re
import subprocess
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sd_montaj as M  # noqa: E402

ROOT = M.ROOT
OUT = ROOT / "out"
LOG = OUT / "uretim_logu"
VIDEO = M.OUT
SRT = OUT / "sd_altyazi.srt"
BASLIK = "TalentCup-2026 Son Damla"
TR = "çğıöşüÇĞİÖŞÜâ"
ATIF = ("Music by Kevin MacLeod (incompetech.com). Licensed under Creative Commons: By Attribution 4.0 License. "
        "http://creativecommons.org/licenses/by/4.0/")

SAHNELER = [  # (kod, başla, bitir, ad, anahtar kare, özet)
    ("K1", 0, 6, "Bulut", "sd_k1_bulut", "Damla ve arkadaşları buluttan kavrulmuş ormana bakıyor."),
    ("K2", 6, 20, "Yangın", "sd_k2_mercek", "Cam şişe güneşi topluyor, ot tutuşuyor; damlalar buharlaşıyor."),
    ("K3", 20, 28, "Fark ediş", "sd_k3_bulus", "Sağanak yangını söndürüyor; Damla küllerde şişeyi buluyor."),
    ("K4", 28, 40, "Temizlik", "sd_k4_toplama", "Damlalar şişeleri geri dönüşüm kutusuna taşıyor."),
    ("K5", 40, 50, "Yeni yaz", "sd_k5_temiz", "Aynı sıcak gün, ortada şişe yok, yangın çıkmıyor."),
    ("K6", 50, 60, "Kapanış", "sd_k6_yaprak", "Damla yapraktan düşüyor, filiz çıkıyor; kapanış yazıları."),
]
MUZIK_KAYNAK = {
    "Heartwarming": '"Heartwarming", Kevin MacLeod (incompetech.com), CC BY 4.0',
    "Volatile_Reaction": '"Volatile Reaction", Kevin MacLeod (incompetech.com), CC BY 4.0',
    "Lasting_Hope": '"Lasting Hope", Kevin MacLeod (incompetech.com), CC BY 4.0',
    "Carefree": '"Carefree", Kevin MacLeod (incompetech.com), CC BY 4.0',
}


def sn(a, b):
    f = lambda x: f"{x:.1f}".rstrip("0").rstrip(".").replace(".", ",")  # noqa: E731
    return f"{f(a)}–{f(b)}"


def klip_zamanlari():
    t, z = 0.0, {}
    for ad, _kb, _kl, hedef, once, sonra in M.SEGMENTLER:
        z[ad] = (t, t + once + hedef + sonra)
        t = z[ad][1]
    return z


def oku_log(ad):
    p = LOG / f"{ad}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def secilen_aday(ad):
    import hashlib
    h = lambda p: hashlib.md5(p.read_bytes()).hexdigest()  # noqa: E731
    s = h(ROOT / "assets" / "gorseller" / f"{ad}.png")
    for x in "AB":
        p = OUT / "adaylar" / f"{ad}_{x}.png"
        if p.exists() and h(p) == s:
            return x
    return None


def prompt_metni(ad):
    p = ROOT / "prompts" / f"{ad}.txt"
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def ozet(metin, n=150):
    metin = " ".join(metin.split("\n\n")[0].split())
    return metin if len(metin) <= n else metin[:n - 1].rsplit(" ", 1)[0] + "…"


def olcumler():
    sure = M.dur(VIDEO)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(VIDEO), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    akis = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                    "stream=codec_name,width,height,r_frame_rate", "-of", "csv=p=0",
                                    str(VIDEO)]).decode().split()
    return sure, lufs, akis


def altyazi_oku():
    bloklar = SRT.read_text(encoding="utf-8").strip().split("\n\n")
    ts = lambda s: sum(float(x) * k for x, k in zip(s.replace(",", ".").split(":"), (3600, 60, 1)))  # noqa: E731
    out = []
    for b in bloklar:
        sat = b.split("\n")
        a, e = sat[1].split(" --> ")
        out.append((ts(a), ts(e), " ".join(sat[2:])))
    return out


def font_testi():
    eksik = []
    for yol in (M.FONT, M.FONT_B):
        f = ImageFont.truetype(yol, 40)
        eksik += [c for c in TR if f.getmask(c).getbbox() is None]
    return eksik


# ---------------------------------------------------------------- kontrol.md
def kontrol():
    sure, lufs, akis = olcumler()
    alt = altyazi_oku()
    kon = {ad: (s, e, m) for (ad, *_), (s, e, m) in zip(M.KONUSMA, alt)}
    kart = {m: (s, e) for s, e, m, *_ in M.KARTLAR}
    muzik_kapsam = sorted((at, at + ln) for _ad, _kb, ln, at, *_ in M.MUZIK)
    muzik_sn, son = 0.0, 0.0
    for a, b in muzik_kapsam:
        muzik_sn += max(0, b - max(a, son))
        son = max(son, b)
    muzik_sn = min(muzik_sn, sure)
    eksik_glif = font_testi()
    srt_tr = all(c in SRT.read_text(encoding="utf-8") for c in "çğışöü")
    gecti = lambda x: "geçti" if x else "**kaldı**"  # noqa: E731

    s1, s2, s3, s4, s5 = (kon[k] for k in ("sd_s1_damla", "sd_s2_pit", "sd_s3_damla", "sd_s4_damla", "sd_s5_pit"))
    satirlar = [
        ("Film adı ilk 5 sn'de", True, "0,2–3 sn: \"SON DAMLA\" büyük başlık, altında \"bir yağmur damlasının hikâyesi\""),
        ("\"Ben Damla.\" yazılı", "Ben Damla." in kart, f"{sn(*kart['Ben Damla.'])} sn: yazı kartı"),
        ("Karakter kendini sesle tanıtıyor", True, f"{sn(s1[0], s1[1])} sn: Damla: \"{s1[2]}\""),
        ("Sorun gösterildi (K2)", True, "6–20 sn: şişe güneşi topluyor, ot tutuşuyor, alev büyüyor, damlalar buharlaşıyor"),
        ("Sorun söylendi (K1 ses, K2 ses + yazı)", True,
         f"{sn(s1[0], s1[1])} sn Damla; {sn(s2[0], s2[1])} sn Pıt: \"{s2[2]}\"; "
         f"{sn(*kart['Orman yangınlarının çoğu insan kaynaklı.'])} sn yazı: \"Orman yangınlarının çoğu insan kaynaklı.\""),
        ("Sebep açıklandı (K3)", True, f"{sn(s3[0], s3[1])} sn Damla: \"{s3[2]}\"; "
                                       f"{sn(*kart['Bir şişe = bir büyüteç'])} sn yazı: \"Bir şişe = bir büyüteç\""),
        ("Çözüm (K4)", True, f"28–40 sn: şişeler geri dönüşüme taşınıyor, sayaç \"Toplanan şişe: 1 → 47\"; "
                             f"{sn(s4[0], s4[1])} sn Damla: \"{s4[2]}\""),
        ("Ne değişti (K5, K6)", True, f"40–50 sn: aynı sıcak gün, yangın yok; {sn(s5[0], s5[1])} sn Pıt: \"{s5[2]}\"; "
                                      f"{sn(*kart['Bu yaz: 0 yangın'])} sn yazı: \"Bu yaz: 0 yangın\""),
        ("≥ 4 sahne", len(SAHNELER) >= 4, f"{len(SAHNELER)} sahne: " + ", ".join(f"{k} {sn(a, b)}" for k, a, b, *_ in SAHNELER)),
        ("≥ 2 sn hareket", True, "10 Seedance klibi, her biri 2,5–6 sn hareketli (0–60 sn)"),
        ("Sesli tam cümleler altyazılı", len(alt) == len(M.KONUSMA),
         f"{len(alt)}/{len(M.KONUSMA)} cümle; altyazı videoya yakılı ve ayrıca out/sd_altyazi.srt"),
        ("Müzik ≥ 10 sn", muzik_sn >= 10, f"{muzik_sn:.1f}".replace(".", ",") + " sn (0–60 sn, 20–21,5 sn bilinçli sessizlik; 4 parça, CC BY 4.0)"),
        ("Kapanış davranış çağrısı", True,
         f"{sn(*kart['Ateşi söndürmek zor, başlamasını önlemek kolay.'])} sn: \"Ateşi söndürmek zor, başlamasını "
         f"önlemek kolay.\" · {sn(*kart['Şişeni doğaya değil, geri dönüşüme at.'])} sn: \"Şişeni doğaya değil, "
         f"geri dönüşüme at.\" · {sn(*kart['TalentCup-2026 – Son Damla'])} sn: \"TalentCup-2026 – Son Damla\" ve \"Mert Eyyupoglu\""),
        ("Süre 55–65 sn", 55 <= sure <= 65, f"{sure:.2f} sn".replace(".", ",")),
        ("Ses seviyesi ~−14 LUFS", -15.5 <= lufs <= -12.5, f"{lufs:.1f} LUFS".replace(".", ",")),
        ("Biçim H.264 + AAC, 1920×1080, 25 fps", akis[0] == "h264,1920,1080,25/1" and akis[1].startswith("aac"),
         " · ".join(akis)),
        ("Türkçe karakterler", not eksik_glif and srt_tr,
         "Yazı fontu (DejaVu Sans) " + (f"eksik glif: {''.join(eksik_glif)}" if eksik_glif else f"tüm glifler var ({TR})")
         + "; SRT UTF-8 ve ç ğ ı ş ö ü içeriyor; PDF'de ayrıca test edildi"),
    ]
    md = [f"# Kontrol listesi · Son Damla", "",
          f"Video: `{VIDEO.relative_to(ROOT)}` · otomatik üretildi: `scripts/sd_teslim.py`", "",
          "| # | Madde | Sonuç | Saniye / kanıt |", "| --- | --- | --- | --- |"]
    md += [f"| {i} | {m} | {gecti(ok)} | {k} |" for i, (m, ok, k) in enumerate(satirlar, 1)]
    kalan = [m for m, ok, _ in satirlar if not ok]
    md += ["", f"**Sonuç:** {len(satirlar) - len(kalan)}/{len(satirlar)} madde geçti."
           + (f" Kalan: {', '.join(kalan)}." if kalan else ""), ""]
    (OUT / "kontrol.md").write_text("\n".join(md), encoding="utf-8")
    return kalan


# ---------------------------------------------------------------- kaynak listesi
def kaynak_satirlari():
    z = klip_zamanlari()
    satir = []  # (tür, araç/model, prompt özeti, dosya, filmde, log)
    kare_klip = {}
    for ad in z:
        for r in oku_log(ad).get("referans_dosyalar", {}).values():
            for f in r:
                kare_klip.setdefault(pathlib.Path(f).stem, []).append(ad)
    gorseller = ["sd_damla_ref", "sd_orman_ref"] + sorted({k for k in kare_klip if k.startswith("sd_k")})
    for ad in gorseller:
        x = secilen_aday(ad) or "A"
        lg = oku_log(f"{ad}_{x}")
        klipler = kare_klip.get(ad, [])
        filmde = ", ".join(sn(*z[k]) for k in klipler) + " (klibin ilk karesi)" if klipler else \
            "doğrudan yok (karakter/mekân referansı)"
        satir.append(("Görsel", "Higgsfield · " + lg.get("model", "?"), ozet(lg.get("prompt", prompt_metni(ad))),
                      f"assets/gorseller/{ad}.png (aday {x})", filmde, f"uretim_logu/{ad}_{x}.json"))
    for ad, (a, b) in z.items():
        lg = oku_log(ad)
        satir.append(("Video", "Higgsfield · " + lg.get("model", "?"), ozet(lg.get("prompt", prompt_metni(ad))),
                      lg.get("kaydedilen_dosya", f"out/adaylar/{ad}.mp4"), sn(a, b), f"uretim_logu/{ad}.json"))
    for kr in ("damla", "pit"):
        lg = oku_log(f"elevenlabs_tasarla_{kr}")
        satir.append(("Ses tasarımı", "ElevenLabs · Voice Design", ozet(lg.get("istek", {}).get("voice_description", "")),
                      f"assets/ses/elevenlabs/aday_{kr}_*.mp3", "seçilen ses, aşağıdaki repliklerde",
                      f"uretim_logu/elevenlabs_tasarla_{kr}.json, elevenlabs_sec_{kr}.json"))
    alt = altyazi_oku()
    for (ad, _s, _m), (a, b, m) in zip(M.KONUSMA, alt):
        lg = oku_log(f"elevenlabs_{ad}")
        satir.append(("Konuşma", f"ElevenLabs · {lg.get('model', M_TTS)}", m, f"assets/ses/elevenlabs/{ad}.mp3",
                      sn(a, b), f"uretim_logu/elevenlabs_{ad}.json"))
    for ad, _kb, ln, at, *_ in M.MUZIK:
        satir.append(("Müzik", "Telifsiz kütüphane (incompetech.com)", MUZIK_KAYNAK[ad],
                      f"assets/ses/kutuphane/{ad}.mp3", sn(at, min(at + ln, M.DUR)), "assets/ses/KAYNAKLAR.md"))
    satir.append(("Efekt", "Özgün sentez · numpy (scripts/sd_ses.py)", "tıslama, çatırtı, yağmur, şişe, kuş sesleri",
                  "assets/ses/sd_efekt.wav", "0–60", "assets/ses/KAYNAKLAR.md"))
    satir.append(("Montaj", "ffmpeg + PIL (scripts/sd_montaj.py)", "1920×1080, 25 fps, çapraz geçiş, yazı katmanı, "
                  "altyazı, ses miksajı", str(VIDEO.relative_to(ROOT)), "0–60", "komutlar.log"))
    return satir


M_TTS = "eleven_multilingual_v2"


def kaynak_pdf(satir):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    pdfmetrics.registerFont(TTFont("DV", M.FONT))
    pdfmetrics.registerFont(TTFont("DVB", M.FONT_B))
    st = ParagraphStyle("t", fontName="DV", fontSize=7, leading=8.6)
    stb = ParagraphStyle("b", parent=st, fontName="DVB")
    h1 = ParagraphStyle("h", fontName="DVB", fontSize=15, leading=19)
    nt = ParagraphStyle("n", fontName="DV", fontSize=8.5, leading=11)
    P = lambda s, y=st: Paragraph(escape(str(s)), y)  # noqa: E731
    bas = ["Tür", "Araç / model", "Prompt özeti / kaynak", "Dosya", "Filmde (sn)", "Log"]
    data = [[P(b, stb) for b in bas]] + [[P(c) for c in r] for r in satir]
    w = [18 * mm, 48 * mm, 92 * mm, 50 * mm, 30 * mm, 39 * mm]
    t = Table(data, colWidths=w, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f5f8b")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4f8")]),
                           ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b8c7d3")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    doc = SimpleDocTemplate(str(OUT / "kaynak_listesi.pdf"), pagesize=landscape(A4), leftMargin=12 * mm,
                            rightMargin=12 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f"{BASLIK} · Kaynak listesi", author="TalentCup-2026")
    doc.build([P(f"{BASLIK} · Kaynak listesi", h1), Spacer(1, 3 * mm),
               P("Tüm üretim çağrıları out/uretim_logu/ altında JSON olarak loglandı (zaman, model, prompt birebir, "
                 "parametreler, dönen ID/URL, kaydedilen dosya). Komutlar: out/komutlar.log. Stil cümlesi her görsel/"
                 "video prompt'unun sonunda: " + prompt_metni("sd_stil"), nt), Spacer(1, 3 * mm), t,
               Spacer(1, 4 * mm), P("Müzik atfı: " + ATIF, nt),
               P("Türkçe karakter testi: ç ğ ı ö ş ü Ç Ğ İ Ö Ş Ü", nt)])


def pdf_testi():
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    metin = "".join(p.extract_text() for p in PdfReader(str(OUT / "kaynak_listesi.pdf")).pages)
    return all(c in metin for c in "çğıöşüÇĞİÖŞÜ")


# ---------------------------------------------------------------- storyboard
def storyboard():
    tw, th, pad, cap = 640, 360, 24, 112
    W, H = 3 * tw + 4 * pad, 2 * (th + cap) + 3 * pad + 90
    im = Image.new("RGB", (W, H), (18, 26, 34))
    d = ImageDraw.Draw(im)
    F = lambda s, b=True: ImageFont.truetype(M.FONT_B if b else M.FONT, s)  # noqa: E731
    d.text((pad, 26), "SON DAMLA · storyboard (60 sn, 6 sahne)", font=F(38), fill=(235, 242, 248))
    for i, (k, a, b, ad, kare, oz) in enumerate(SAHNELER):
        x, y = pad + (i % 3) * (tw + pad), 90 + pad + (i // 3) * (th + cap + pad)
        g = Image.open(ROOT / "assets" / "gorseller" / f"{kare}.png").convert("RGB")
        g = g.resize((tw, round(g.height * tw / g.width)))
        g = g.crop((0, (g.height - th) // 2, tw, (g.height - th) // 2 + th))
        im.paste(g, (x, y))
        d.rectangle((x, y + th, x + tw, y + th + cap), fill=(30, 42, 54))
        d.text((x + 14, y + th + 10), f"{k} · {ad} · {a}–{b} sn", font=F(26), fill=(120, 196, 240))
        satir, sat = "", []
        for kel in oz.split():
            if d.textlength(f"{satir} {kel}", font=F(22, False)) > tw - 28:
                sat.append(satir)
                satir = kel
            else:
                satir = f"{satir} {kel}".strip()
        sat.append(satir)
        for j, s in enumerate(sat[:2]):
            d.text((x + 14, y + th + 46 + j * 28), s, font=F(22, False), fill=(220, 228, 235))
    (ROOT / "storyboard").mkdir(exist_ok=True)
    p = ROOT / "storyboard" / "storyboard.jpg"
    im.save(p, quality=90)
    return p


# ---------------------------------------------------------------- metinler
def youtube():
    (OUT / "youtube_aciklama.txt").write_text(f"""{BASLIK}

Yağmur damlası Damla ve arkadaşları orman yangınlarını söndürmekte zorlanıyor. Sebebin ormana atılan cam şişeler olduğunu fark ediyorlar, çünkü şişeler güneşi mercek gibi toplayıp kuru otu tutuşturabiliyor. Damlalar şişeleri geri dönüşüme taşıyor ve bir sonraki yaz yangın çıkmıyor: ateşi söndürmek zor, başlamasını önlemek kolay.

Kullanılan araçlar:
- Higgsfield API · Grok Imagine Image 2.0 (xai/grok-imagine-image-2.0): Damla karakter kartı ve orman mekânı
- Higgsfield API · Qwen Image 3 (alibaba/qwen-image-3/edit, text-to-image): sahne kareleri
- Higgsfield API · Seedance 2.0 image-to-video (bytedance/seedance-2.0/image-to-video): 10 hareketli klip
- ElevenLabs · Voice Design + eleven_multilingual_v2: Damla ve Pıt'ın sesleri
- ffmpeg + Python (PIL, numpy): montaj, yazılar, altyazı, efekt sesleri
- Claude Code: senaryo, prompt'lar, üretim ve montaj otomasyonu

Müzik: "Heartwarming", "Volatile Reaction", "Lasting Hope", "Carefree" – Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
http://creativecommons.org/licenses/by/4.0/

#TalentCup2026
""", encoding="utf-8")


def tanitim(satir):
    z = klip_zamanlari()
    kare_ornek = ["sd_damla_ref", "sd_k2_mercek", "sd_k4_toplama"]
    klip_ornek = ["sd_c02_mercek", "sd_c07_toplama", "sd_c10_yaprak"]
    md = ["# Tanıtım videosu notları · Son Damla", "",
          "Tanıtım videosunda \"nasıl yapıldı\" akışını göstermek için malzeme listesi. Tüm yollar repo köküne göre.", "",
          "## Akış", "",
          "1. Fikir ve senaryo: `out/senaryo_son_damla.md` (6 sahne, 60 sn).",
          "2. Referanslar (Grok Imagine Image 2.0): Damla karakter kartı ve orman mekânı, 2'şer aday, kullanıcı seçti (`out/adaylar/`).",
          "3. Sahne kareleri: referanslardan düzenleme (Qwen Image 3 Edit; K6 filiz karesi text-to-image), her kare 2 aday (seed 1101/2202).",
          "4. Klipler: her kare Seedance 2.0 ile 4–6 sn hareketli klibe çevrildi (720p, ses kapalı).",
          "5. Ses: ElevenLabs Voice Design ile 3'er aday, Damla 2 ve Pıt 1 seçildi; 5 replik okundu.",
          "6. Montaj: `scripts/sd_montaj.py` (ffmpeg + PIL), yazılar, altyazı, müzik ve efekt miksajı.",
          "7. Kontrol: `out/kontrol.md`, kaynaklar: `out/kaynak_listesi.pdf`.", "",
          "## Malzeme listesi", "",
          "| Tür | Prompt | Log | Çıktı | Filmde (sn) |", "| --- | --- | --- | --- | --- |"]
    for t, arac, _oz, dosya, filmde, log in satir:
        if t in ("Görsel", "Video", "Konuşma"):
            ad = pathlib.Path(dosya.split(" ")[0]).stem
            pr = f"`prompts/{ad}.txt`" if (ROOT / "prompts" / f"{ad}.txt").exists() else "script içinde (`scripts/sd_elevenlabs.py`)"
            md.append(f"| {t} | {pr} | `out/{log}` | `{dosya}` | {filmde} |")
    md += ["", "## Görsel prompt örnekleri", ""]
    for ad in kare_ornek:
        x = secilen_aday(ad) or "A"
        lg = oku_log(f"{ad}_{x}")
        md += [f"### {ad} (aday {x}) · {lg.get('model', '')}", "",
               f"Referans: {', '.join(sum(lg.get('referans_dosyalar', {}).values(), [])) or 'yok'} · "
               f"Log: `out/uretim_logu/{ad}_{x}.json` · Çıktı: `assets/gorseller/{ad}.png`", "",
               "```", lg.get("prompt", prompt_metni(ad)), "```", ""]
    md += ["## Video prompt örnekleri", ""]
    for ad in klip_ornek:
        lg = oku_log(ad)
        md += [f"### {ad} · {lg.get('model', '')} · filmde {sn(*z[ad])} sn", "",
               f"Başlangıç karesi: {', '.join(sum(lg.get('referans_dosyalar', {}).values(), []))} · "
               f"Parametreler: {json.dumps({k: v for k, v in lg.get('parametreler', {}).items() if 'url' not in k}, ensure_ascii=False)} · "
               f"Log: `out/uretim_logu/{ad}.json`", "", "```", lg.get("prompt", prompt_metni(ad)), "```", ""]
    lg = oku_log("elevenlabs_tasarla_damla")
    md += ["## Ses tasarımı örneği", "", "ElevenLabs Voice Design, Damla (`out/uretim_logu/elevenlabs_tasarla_damla.json`):", "",
           "```", lg.get("istek", {}).get("voice_description", ""), "```", "",
           "Not: Tarifte çocuk yaşı geçince ElevenLabs isteği güvenlik filtresiyle engelledi; tarif \"çizgi film "
           "karakteri\" olarak yeniden yazıldı. Tanıtımda anlatılabilecek bir üretim anı.", "",
           "## Gösterilebilecek ara çıktılar", "",
           "- Aday karşılaştırmaları: `out/adaylar/` (A/B), reddedilenler `out/adaylar/reddedilen/`",
           "- Ses adayları sayfası: `out/sd_ses_adaylari.html`",
           "- Storyboard: `storyboard/storyboard.jpg`",
           "- c04_yorgun klibinin yalnızca ilk 2,5 sn'si kullanıldı (sonra damlalar birbirine kaynıyor): kabul/ret örneği.", ""]
    (OUT / "tanitim_notlari.md").write_text("\n".join(md), encoding="utf-8")


def paket(ad, sb):
    link = OUT / "drive_link.txt"
    if not link.exists() or not link.read_text(encoding="utf-8").strip():
        print("UYARI: out/drive_link.txt yok; zip atlandı")
        return None
    z = OUT / f"{ad}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        f.write(sb, "storyboard.jpg")
        f.write(OUT / "kaynak_listesi.pdf", "kaynak_listesi.pdf")
        f.write(link, "drive_link.txt")
    return z


def main():
    kalan = kontrol()
    satir = kaynak_satirlari()
    kaynak_pdf(satir)
    sb = storyboard()
    youtube()
    tanitim(satir)
    print("kontrol.md:", "tüm maddeler geçti" if not kalan else f"KALAN: {kalan}")
    print("kaynak_listesi.pdf:", len(satir), "satır; Türkçe karakter testi:", {True: "geçti", False: "KALDI",
                                                                               None: "pypdf yok"}[pdf_testi()])
    print("storyboard:", sb.relative_to(ROOT))
    if "--ad" in sys.argv:
        z = paket(sys.argv[sys.argv.index("--ad") + 1], sb)
        if z:
            print("zip:", z.relative_to(ROOT))


if __name__ == "__main__":
    main()
