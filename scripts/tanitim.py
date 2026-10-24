#!/usr/bin/env python3
"""Son Damla tanıtım videosu (yarışma şartı 3): Mert'in sesiyle anlatılan "nasıl yaptım" videosu.

  tanitim.py metin     out/tanitim/anlatim_metni.md (kayıt rehberi + okunacak metin)
  tanitim.py           kayıt varsa final, yoksa önizleme üretir
                       kayıtlar: assets/ses/tanitim/t01.m4a … t13.m4a (t03 yok: orada filmin kendi sesi çalar)
                       final:     out/tanitim/TalentCup-2026_Son_Damla_Tanitim.mp4
                       önizleme:  out/tanitim/tanitim_onizleme.mp4 (sessiz anlatım, metin altyazıda, filigranlı)
  --altyazi            finalde de anlatım metnini altyazı olarak yaz

Her bölümün süresi kaydın uzunluğuna göre ayarlanır (kayıt + 0,8 sn); kayıt yoksa okuma hızından tahmin edilir.
Tekrar çalıştırılabilir; ara dosyalar work/tanitim/.
"""
import json
import pathlib
import subprocess
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sd_montaj as M  # noqa: E402
import sd_teslim as T  # noqa: E402

ROOT = M.ROOT
W, H, FPS = 1920, 1080, 25
WORK = ROOT / "work" / "tanitim"
OUTD = ROOT / "out" / "tanitim"
KAYIT = ROOT / "assets" / "ses" / "tanitim"
FILM = M.OUT
G = ROOT / "assets" / "gorseller"
ADAY = ROOT / "out" / "adaylar"
FONT_B, FONT, MONO = M.FONT_B, M.FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
OKUMA_HIZI = 2.2  # kelime/sn, kayıt yokken süre tahmini
PAY = 0.8          # kaydın sonuna eklenen nefes payı (sn)
ENC = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS)]

MAVI, SARI, BEYAZ, GRI = (120, 196, 240), (255, 205, 80), (240, 245, 250), (170, 185, 200)


def F(s, kalin=True, mono=False):
    return ImageFont.truetype(MONO if mono else (FONT_B if kalin else FONT), s)


# ---------------------------------------------------------------- çizim yardımcıları
def arka():
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(14 + 8 * k), int(26 + 22 * k), int(40 + 34 * k)))
    return im


def bulanik_arka(gorsel, karart=0.45):
    g = Image.open(gorsel).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(14))
    return Image.blend(g, Image.new("RGB", (W, H), (8, 14, 22)), karart)


def ortala(d, y, metin, font, renk=BEYAZ):
    d.text((W / 2 + 3, y + 3), metin, font=font, fill=(0, 0, 0), anchor="mm")
    d.text((W / 2, y), metin, font=font, fill=renk, anchor="mm")


def baslik(im, no, metin, alt=None):
    d = ImageDraw.Draw(im)
    d.text((70, 52), f"{no:02d}", font=F(30), fill=SARI)
    d.text((130, 40), metin, font=F(52), fill=BEYAZ)
    if alt:
        d.text((132, 108), alt, font=F(28, False), fill=GRI)
    return d


def sar(d, metin, font, genislik):
    satirlar = []
    for paragraf in metin.split("\n"):
        satir = ""
        for kel in paragraf.split():
            aday = f"{satir} {kel}".strip()
            if d.textlength(aday, font=font) > genislik and satir:
                satirlar.append(satir)
                satir = kel
            else:
                satir = aday
        satirlar.append(satir)
    return satirlar


def yerlestir(im, yol, kutu, cerceve=MAVI, kalinlik=4):
    """Görseli kutuya oranını koruyarak sığdırır; gerçek yerleşim dikdörtgenini döner."""
    x, y, w, h = kutu
    g = Image.open(yol).convert("RGB") if not isinstance(yol, Image.Image) else yol
    s = min(w / g.width, h / g.height)
    g = g.resize((round(g.width * s), round(g.height * s)), Image.LANCZOS)
    gx, gy = x + (w - g.width) // 2, y + (h - g.height) // 2
    d = ImageDraw.Draw(im)
    if cerceve:
        d.rectangle((gx - kalinlik, gy - kalinlik, gx + g.width + kalinlik - 1, gy + g.height + kalinlik - 1), fill=cerceve)
    im.paste(g, (gx, gy))
    return gx, gy, g.width, g.height


def rozet(d, xy, metin, font=None, renk=SARI, yazi=(20, 24, 30), anchor="la"):
    font = font or F(30)
    x0, y0, x1, y1 = d.textbbox(xy, metin, font=font, anchor=anchor)
    d.rounded_rectangle((x0 - 16, y0 - 10, x1 + 16, y1 + 10), radius=12, fill=renk)
    d.text(xy, metin, font=font, fill=yazi, anchor=anchor)


def kod_kutusu(im, kutu, ust, metin, font_boyu=22, max_satir=14):
    x, y, w, h = kutu
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x, y, x + w, y + h), radius=16, fill=(8, 14, 20), outline=(60, 90, 120), width=2)
    d.text((x + 24, y + 18), ust, font=F(24), fill=SARI)
    f = F(font_boyu, mono=True)
    kar = int((w - 48) / f.getlength("M"))
    satirlar = []
    for p in metin.split("\n"):
        satirlar += textwrap.wrap(p, kar) or [""]
    if len(satirlar) > max_satir:
        satirlar = satirlar[:max_satir - 1] + [satirlar[max_satir - 1][:kar - 1] + "…"]
    for i, s in enumerate(satirlar):
        d.text((x + 24, y + 64 + i * (font_boyu + 9)), s, font=f, fill=(200, 230, 210))


def adim_seridi(d, aktif):
    adimlar = ["1  Storyboard karesi", "2  Görsel (Qwen Image 3)", "3  Klip (Seedance 2.0)", "4  Final film"]
    x = 130
    for i, a in enumerate(adimlar):
        f = F(28)
        w = d.textlength(a, font=f) + 40
        d.rounded_rectangle((x, 150, x + w, 200), radius=25,
                            fill=SARI if i == aktif else (34, 52, 70))
        d.text((x + 20, 175), a, font=f, fill=(20, 24, 30) if i == aktif else GRI, anchor="lm")
        if i < len(adimlar) - 1:
            d.text((x + w + 14, 175), "→", font=f, fill=GRI, anchor="lm")
        x += w + 56


def prompt_ilk(ad):
    return T.prompt_metni(ad).split("\n\n")[0]


def model_adi(log):
    m = log.get("model", "")
    return {"xai/grok-imagine-image-2.0": "Grok Imagine Image 2.0", "alibaba/qwen-image-3/edit": "Qwen Image 3 Edit",
            "alibaba/qwen-image-3/text-to-image": "Qwen Image 3",
            "bytedance/seedance-2.0/image-to-video": "Seedance 2.0"}.get(m, m)


# ---------------------------------------------------------------- planlar (her biri bir PNG ya da PNG + video)
SB_KUTU = (130, 230, 1660, 800)  # storyboard'un ekrandaki yeri


def sb_k2_dikdortgen(gx, gy, gw, _gh):
    s = gw / 2016  # storyboard.jpg 2016 px genişliğinde; K2 ikinci sütun, ilk satır (sd_teslim.storyboard)
    tw, th, pad, cap = 640, 360, 24, 112
    x0, y0 = pad + (tw + pad), 90 + pad
    return gx + x0 * s, gy + y0 * s, gx + (x0 + tw) * s, gy + (y0 + th + cap) * s


def kart_acilis():
    im = bulanik_arka(G / "sd_k1_bulut.png", .5)
    d = ImageDraw.Draw(im)
    ortala(d, 400, "SON DAMLA", F(150))
    ortala(d, 530, "Filmimi nasıl yaptım?", F(60, False))
    ortala(d, 660, "Mert Eyyupoglu · TalentCup-2026", F(40, False), MAVI)
    return im


def kart_storyboard(vurgula):
    im = arka()
    baslik(im, 4, "Storyboard", "6 sahne, her sahne için bir anahtar kare")
    r = yerlestir(im, ROOT / "storyboard" / "storyboard.jpg", SB_KUTU, cerceve=None)
    if vurgula:
        d = ImageDraw.Draw(im, "RGBA")
        d.rectangle((r[0], r[1], r[0] + r[2], r[1] + r[3]), fill=(0, 0, 0, 120))
        x0, y0, x1, y1 = sb_k2_dikdortgen(*r)
        im.paste(Image.open(ROOT / "storyboard" / "storyboard.jpg").convert("RGB").resize(
            (round(r[2]), round(r[3]))).crop((round(x0 - r[0]), round(y0 - r[1]), round(x1 - r[0]), round(y1 - r[1]))),
            (round(x0), round(y0)))
        d.rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 6), outline=SARI, width=8)
        rozet(d, ((x0 + x1) / 2, y1 + 50), "Bu kareyi takip edelim", anchor="mm")
    return im


def kart_adim(aktif, icerik):
    im = arka()
    d = baslik(im, 5, "Bir kare nasıl sahneye dönüştü?", "Örnek: 2. sahne, yangının başladığı an")
    adim_seridi(d, aktif)
    icerik(im, ImageDraw.Draw(im))
    return im


def adim1(im, d):
    sb = Image.open(ROOT / "storyboard" / "storyboard.jpg").convert("RGB")
    x0, y0, x1, y1 = sb_k2_dikdortgen(0, 0, 2016, 1106)
    yerlestir(im, sb.crop((round(x0), round(y0), round(x1), round(y1))), (360, 250, 1200, 760))


def adim2(im, d):
    lg = T.oku_log("sd_k2_mercek_A")
    yerlestir(im, G / "sd_k2_mercek.png", (90, 250, 1000, 720))
    kod_kutusu(im, (1130, 250, 700, 560), f"prompts/sd_k2_mercek.txt · {model_adi(lg)}", prompt_ilk("sd_k2_mercek"),
               font_boyu=20, max_satir=17)
    for i, s in enumerate(sar(d, "Türkçesi: " + T.OZET_TR["sd_k2_mercek"], F(28, False), 1740)[:3]):
        d.text((90, 860 + i * 40), s, font=F(28, False), fill=BEYAZ)


def kart_araclar():
    im = arka()
    d = baslik(im, 6, "Kullandığım araçlar")
    satirlar = [
        ("Claude", "Senaryo, prompt yazma ve montaj"),
        ("Higgsfield", "Görseller ve videolar"),
        ("ElevenLabs", "Damla ve Pıt'ın sesleri"),
        ("Babam", "Her adımda yardım etti"),
    ]
    for i, (k, v) in enumerate(satirlar):
        y = 220 + i * 160
        d.rounded_rectangle((260, y, 1660, y + 130), radius=22, fill=(26, 42, 58) if k != "Babam" else (70, 56, 24))
        d.text((320, y + 65), k, font=F(56), fill=SARI, anchor="lm")
        d.text((760, y + 65), v, font=F(44, False), fill=BEYAZ, anchor="lm")
    d.text((W / 2, 900), "Higgsfield modelleri: Grok Imagine, Qwen Image, Seedance 2.0 · Montaj: ffmpeg + Python",
           font=F(28, False), fill=GRI, anchor="mm")
    d.text((W / 2, 945), "Müzik: Kevin MacLeod (incompetech.com), CC BY 4.0", font=F(28, False), fill=GRI, anchor="mm")
    return im


def kart_gorsel_prompt(no, sira, ad):
    x = T.secilen_aday(ad) or "A"
    lg = T.oku_log(f"{ad}_{x}")
    im = arka()
    d = baslik(im, no, f"Görsel prompt {sira}", f"{model_adi(lg)} · log: out/uretim_logu/{ad}_{x}.json")
    kod_kutusu(im, (90, 170, 860, 640), f"prompts/{ad}.txt", prompt_ilk(ad), font_boyu=21, max_satir=19)
    yerlestir(im, G / f"{ad}.png", (1010, 200, 820, 560))
    rozet(d, (1420, 800), f"Sonuç · seçilen aday {x}", anchor="mm")
    for i, s in enumerate(sar(d, "Türkçesi: " + T.OZET_TR[ad], F(27, False), 1740)[:3]):
        d.text((90, 880 + i * 38), s, font=F(27, False), fill=BEYAZ)
    return im


def kart_adaylar(no, sira, ad):
    x = T.secilen_aday(ad) or "A"
    im = arka()
    d = baslik(im, no, f"Görsel prompt {sira} · iki aday", "Her görsel için 2 aday ürettim, birini seçtim")
    for i, a in enumerate("AB"):
        kx = 90 + i * 890
        r = yerlestir(im, ADAY / f"{ad}_{a}.png", (kx, 230, 850, 560), cerceve=SARI if a == x else (60, 80, 100),
                      kalinlik=8 if a == x else 3)
        rozet(d, (r[0] + r[2] / 2, r[1] + r[3] + 60), f"Aday {a}" + (" · seçildi ✓" if a == x else ""),
              renk=SARI if a == x else (60, 80, 100), yazi=(20, 24, 30) if a == x else BEYAZ, anchor="mm")
    return im


def kart_video_prompt(no, sira, ad):
    lg = T.oku_log(ad)
    im = arka()
    d = baslik(im, no, f"Video prompt {sira}", f"{model_adi(lg)} · log: out/uretim_logu/{ad}.json")
    kod_kutusu(im, (90, 170, 780, 400), f"prompts/{ad}.txt", prompt_ilk(ad), font_boyu=22, max_satir=10)
    bas = sum(lg.get("referans_dosyalar", {}).values(), [])
    d.text((90, 600), "Başlangıç karesi:", font=F(28), fill=SARI)
    if bas:
        yerlestir(im, ROOT / bas[0], (90, 650, 420, 236), kalinlik=3)
    p = {k: v for k, v in lg.get("parametreler", {}).items() if "url" not in k}
    d.text((540, 650), "\n".join(f"{k}: {v}" for k, v in p.items()), font=F(26, mono=True), fill=GRI, spacing=10)
    for i, s in enumerate(sar(d, "Türkçesi: " + T.OZET_TR[ad], F(27, False), 1740)[:3]):
        d.text((90, 920 + i * 38), s, font=F(27, False), fill=BEYAZ)
    d.rounded_rectangle((935, 205, 1835, 711), radius=8, fill=MAVI)
    rozet(d, (1385, 770), "Sonuç: üretilen klip", anchor="mm")
    return im


VIDEO_KUTU = (940, 210, 890, 496)  # kart_video_prompt'taki klip yeri (16:9)


def kart_log():
    lg = T.oku_log("sd_c07_toplama")
    ozet = {k: lg[k] for k in ("zaman", "bitis", "model", "prompt_dosyasi") if k in lg}
    ozet["prompt"] = lg.get("prompt", "")[:150] + "…"
    ozet["parametreler"] = {k: v for k, v in lg.get("parametreler", {}).items() if "url" not in k}
    ozet["referans_dosyalar"] = lg.get("referans_dosyalar")
    ozet["request_id"] = lg.get("request_id")
    ozet["durum"] = lg.get("durum")
    ozet["kaydedilen_dosya"] = lg.get("kaydedilen_dosya")
    im = arka()
    d = baslik(im, 11, "Üretim kayıtları", "Her API çağrısı bir JSON dosyasına yazıldı: toplam "
               f"{len(list((ROOT / 'out' / 'uretim_logu').glob('sd_*.json')))} görsel ve video kaydı")
    kod_kutusu(im, (90, 170, 1740, 860), "out/uretim_logu/sd_c07_toplama.json",
               json.dumps(ozet, ensure_ascii=False, indent=2), font_boyu=24, max_satir=24)
    return im


def kart_kaynak():
    WORK.mkdir(parents=True, exist_ok=True)
    png = WORK / "kaynak_s1"
    subprocess.run(["pdftoppm", "-r", "110", "-png", "-f", "1", "-l", "1", "-singlefile",
                    str(ROOT / "out" / "kaynak_listesi.pdf"), str(png)], check=True)
    im = arka()
    d = baslik(im, 11, "Kaynak listesi", "Bütün kayıtlar tek bir PDF'te: araç, prompt, dosya, filmdeki saniye")
    yerlestir(im, f"{png}.png", (130, 170, 1660, 860), cerceve=(200, 210, 220), kalinlik=2)
    return im


def kart_zaman_cizelgesi():
    im = arka()
    d = baslik(im, 12, "Filmde nerede kullanıldı?", "Final film, 0–60. saniye")
    x0, x1, y = 120, 1800, 690
    sx = lambda t: x0 + (x1 - x0) * t / 60  # noqa: E731
    renkler = [(70, 110, 160), (190, 90, 50), (110, 90, 140), (60, 140, 110), (90, 150, 70), (150, 130, 60)]
    for (k, a, b, ad, *_), r in zip(T.SAHNELER, renkler):
        d.rectangle((sx(a), y, sx(b), y + 70), fill=r)
        d.text(((sx(a) + sx(b)) / 2, y + 35), f"{k} {ad}", font=F(26), fill=BEYAZ, anchor="mm")
    for t in range(0, 61, 10):
        d.text((sx(t), y + 100), f"{t}", font=F(26, False), fill=GRI, anchor="mm")
    isaretler = [(6.0, "sd_k2_mercek", "6. sn · mercek karesi + klibi"),
                 (28.0, "sd_k4_toplama", "28. sn · toplama karesi + klibi"),
                 (50.0, "sd_k6_yaprak", "50. sn · yaprak karesi + klibi")]
    for i, (t, ad, etiket) in enumerate(isaretler):
        cx = 330 + i * 630
        r = yerlestir(im, G / f"{ad}.png", (cx - 260, 220, 520, 292), kalinlik=4)
        d.line((cx, r[1] + r[3] + 4, sx(t), y), fill=SARI, width=5)
        d.ellipse((sx(t) - 10, y - 10, sx(t) + 10, y + 10), fill=SARI)
        rozet(d, (cx, 552), etiket, font=F(26), anchor="mm")
    d.text((W / 2, 900), "Damla'nın karakter kartı (sd_damla_ref) bütün sahnelerde referans olarak kullanıldı.",
           font=F(30, False), fill=BEYAZ, anchor="mm")
    return im


def kart_kapanis():
    im = bulanik_arka(G / "sd_k6_yaprak.png", .55)
    d = ImageDraw.Draw(im)
    ortala(d, 330, "Ateşi söndürmek zor,", F(76))
    ortala(d, 430, "başlamasını önlemek kolay.", F(76))
    ortala(d, 600, "İzlediğiniz için teşekkürler!", F(54, False), SARI)
    ortala(d, 700, "Mert Eyyupoglu · TalentCup-2026 – Son Damla", F(40, False), MAVI)
    ortala(d, 1010, "Müzik: Kevin MacLeod (incompetech.com), CC BY 4.0", F(26, False), GRI)
    return im


def rozet_katmani(metin, konum="ust"):
    """Tam ekran film planları için şeffaf rozet katmanı."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rozet(d, (60, 60) if konum == "ust" else (60, H - 110), metin, font=F(36))
    return im


# ---------------------------------------------------------------- bölümler
# plan: (tür, ağırlık, ...)  tür: "kart" (PIL görseli) | "film" (final filmden kesit, tam ekran)
#       | "klip" (PIL arka planı + kutuda video)
BOLUMLER = [
    dict(ad="t01", baslik="Açılış", planlar=[("kart", 1, kart_acilis)],
         metin="Merhaba, ben Mert. TalentCup için Son Damla adında bir dakikalık bir animasyon film yaptım. "
               "Bu videoda filmimi nasıl yaptığımı anlatacağım."),
    dict(ad="t02", baslik="Filmin konusu", planlar=[("film", 1, 0.0, lambda: rozet_katmani("Filmin konusu"))],
         metin="Filmin kahramanı Damla adında bir yağmur damlası. Damla ve arkadaşları orman yangınlarını "
               "söndürmekte çok zorlanıyor. Sonra yangını başlatan şeyin ormana atılan cam şişeler olduğunu fark "
               "ediyorlar, çünkü cam şişe güneşi büyüteç gibi topluyor. Şimdi filmden kısa bir bölüm izleyelim."),
    dict(ad="t03", baslik="Filmden bir bölüm (anlatım yok, filmin kendi sesi)", sabit=14.0, film_sesi=20.0,
         planlar=[("film", 1, 20.0, lambda: rozet_katmani("Filmden bir bölüm · 20–34. saniye"))],
         metin=""),
    dict(ad="t04", baslik="Storyboard", planlar=[("kart", 1, lambda: kart_storyboard(False)),
                                                 ("kart", 1, lambda: kart_storyboard(True))],
         metin="Önce filmi altı sahneye böldüm ve bir storyboard hazırladım. Her sahne için bir anahtar kare var: "
               "bulut, yangın, fark ediş, temizlik, yeni yaz ve kapanış."),
    dict(ad="t05", baslik="Bir kare nasıl sahneye dönüştü?",
         planlar=[("kart", 1, lambda: kart_adim(0, adim1)),
                  ("kart", 1.3, lambda: kart_adim(1, adim2)),
                  ("klip", 1.2, lambda: kart_adim(2, lambda im, d: d.rounded_rectangle(
                      (355, 245, 1565, 925), radius=8, fill=MAVI)), ADAY / "sd_c02_mercek.mp4", 0.0, (360, 250, 1200, 675)),
                  ("klip", 1.2, lambda: kart_adim(3, lambda im, d: (d.rounded_rectangle(
                      (355, 245, 1565, 925), radius=8, fill=SARI), rozet(d, (960, 975), "Filmde 6–11,5. saniye",
                                                                          anchor="mm"))), FILM, 6.0, (360, 250, 1200, 675))],
         metin="Mesela ikinci sahnedeki bu kareye bakalım. Önce yapay zekâya, şişeden geçen güneşin kuru otu "
               "yaktığı bir görsel çizdirdim. Sonra bu görseli video modeline verip alevin büyümesini istedim. "
               "Bu klip filmin altıncı saniyesinde başlıyor."),
    dict(ad="t06", baslik="Araçlar", planlar=[("kart", 1, kart_araclar)],
         metin="Bu filmi Claude, Higgsfield ve ElevenLabs kullanarak, babamın yardımıyla yaptım. Görselleri ve "
               "videoları Higgsfield ile, karakterlerin seslerini ElevenLabs ile yaptım. Claude da prompt yazmama ve "
               "montaja yardım etti."),
    dict(ad="t07", baslik="Görsel prompt 1", planlar=[("kart", 1.4, lambda: kart_gorsel_prompt(7, 1, "sd_damla_ref")),
                                                      ("kart", 1, lambda: kart_adaylar(7, 1, "sd_damla_ref"))],
         metin="İlk görsel promptum Damla'nın karakter kartı. İki aday ürettim ve en beğendiğimi seçtim. Damla her "
               "sahnede aynı görünsün diye bu kartı referans olarak kullandım."),
    dict(ad="t08", baslik="Görsel prompt 2", planlar=[("kart", 1.4, lambda: kart_gorsel_prompt(8, 2, "sd_k4_toplama")),
                                                      ("kart", 1, lambda: kart_adaylar(8, 2, "sd_k4_toplama"))],
         metin="İkinci görsel promptum dördüncü sahne: damlalar küçük bir dere olup şişeleri geri dönüşüm kutusuna "
               "taşıyor. Burada da iki adaydan birini seçtim."),
    dict(ad="t09", baslik="Video prompt 1",
         planlar=[("klip", 1, lambda: kart_video_prompt(9, 1, "sd_c07_toplama"), ADAY / "sd_c07_toplama.mp4", 0.0,
                   VIDEO_KUTU)],
         metin="İlk video promptumda, damlaların deresi şişeleri kutuya doğru yuvarlıyor. Damla da kameraya dönüp "
               "konuşuyor. Başlangıç karesi olarak bir önceki görseli verdim."),
    dict(ad="t10", baslik="Video prompt 2",
         planlar=[("klip", 1, lambda: kart_video_prompt(10, 2, "sd_c10_yaprak"), ADAY / "sd_c10_yaprak.mp4", 0.0,
                   VIDEO_KUTU)],
         metin="İkinci video promptumda Damla göz kırpıyor, yapraktan düşüyor ve düştüğü yerde bir filiz çıkıyor. "
               "Bu, filmin son sahnesi."),
    dict(ad="t11", baslik="Üretim kayıtları", planlar=[("kart", 1.2, kart_log), ("kart", 1, kart_kaynak)],
         metin="Her üretimin kaydını tuttum. Kayıtlarda zaman, model, promptun tamamı ve çıkan dosyanın adı yazıyor. "
               "Sonra hepsini bir kaynak listesinde topladım."),
    dict(ad="t12", baslik="Filmde nerede kullanıldı?",
         planlar=[("kart", 1.3, kart_zaman_cizelgesi),
                  ("film", 1, 28.0, lambda: rozet_katmani("Filmde 28. saniye · toplama karesi ve klibi", "alt")),
                  ("film", 1, 50.0, lambda: rozet_katmani("Filmde 50. saniye · yaprak karesi ve klibi", "alt"))],
         metin="Son olarak bu görsel ve videoların filmde nerede olduğuna bakalım. Mercek sahnesi altıncı saniyede, "
               "toplama sahnesi yirmi sekizinci saniyede, son sahne de ellinci saniyede başlıyor."),
    dict(ad="t13", baslik="Kapanış", planlar=[("kart", 1, kart_kapanis)],
         metin="Filmimin mesajı şu: Ateşi söndürmek zor, başlamasını önlemek kolay. İzlediğiniz için teşekkürler!"),
]


# ---------------------------------------------------------------- süre ve ses
def kayit_dosyasi(ad):
    for uz in ("m4a", "mp3", "wav", "aac", "ogg", "opus", "webm", "mp4", "mov", "3gp", "amr"):
        p = KAYIT / f"{ad}.{uz}"
        if p.exists():
            return p
    return None


def hazir_kayit(ad):
    """Kaydın başındaki ve sonundaki sessizliği kırpar (-40 dB, 0,15 sn pay bırakır) → work/tanitim/kayit/<ad>.wav."""
    k = kayit_dosyasi(ad)
    if not k:
        return None
    out = WORK / "kayit" / f"{ad}.wav"
    if not out.exists() or out.stat().st_mtime < k.stat().st_mtime:
        out.parent.mkdir(parents=True, exist_ok=True)
        kirp = "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.15"
        ff("-i", k, "-af", f"{kirp},areverse,{kirp},areverse", "-ar", 48000, out)
    return out


def sure(b):
    if "sabit" in b:
        return b["sabit"]
    k = hazir_kayit(b["ad"])
    if k:
        return M.dur(k) + PAY
    return round(len(b["metin"].split()) / OKUMA_HIZI + 1.0, 2)


def ff(*args):
    cmd = ["ffmpeg", "-v", "error", "-y", *map(str, args)]
    M.log(cmd)
    subprocess.run(cmd, check=True, cwd=ROOT)


# ---------------------------------------------------------------- görüntü
def plan_videosu(b, i, plan, d):
    out = WORK / f"{b['ad']}_p{i}.mp4"
    tur = plan[0]
    if tur == "kart":
        png = WORK / f"{b['ad']}_p{i}.png"
        plan[2]().save(png)
        ff("-loop", 1, "-framerate", FPS, "-t", d, "-i", png, *ENC, "-t", d, out)
    elif tur == "film":
        katman = WORK / f"{b['ad']}_p{i}_k.png"
        plan[3]().save(katman)
        ff("-ss", plan[2], "-t", d, "-i", FILM, "-loop", 1, "-framerate", FPS, "-t", d, "-i", katman,
           "-filter_complex", f"[0:v]fps={FPS},setpts=N/{FPS}/TB,tpad=stop_mode=clone:stop_duration={d}[f];"
                              "[f][1:v]overlay=format=auto[v]", "-map", "[v]", "-an", *ENC, "-t", d, out)
    elif tur == "klip":
        _t, _w, bg, video, ss, (x, y, w, h) = plan
        png = WORK / f"{b['ad']}_p{i}.png"
        bg().save(png)
        ff("-loop", 1, "-framerate", FPS, "-t", d, "-i", png, "-ss", ss, "-t", d, "-i", video,
           "-filter_complex", f"[1:v]fps={FPS},setpts=N/{FPS}/TB,scale={w}:{h},tpad=stop_mode=clone:stop_duration={d}[c];"
                              f"[0:v][c]overlay={x}:{y}:eof_action=repeat[v]", "-map", "[v]", "-an", *ENC, "-t", d, out)
    return out


def altyazi_katmanlari(b, d, filigran):
    """Metni ≤ 12 kelimelik parçalara böler, kelime sayısına göre zamanlar; (png, başla, bitir) listesi."""
    out = []
    if filigran:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((W - 40, 40), "ÖNİZLEME · anlatım: Mert'in sesi eklenecek", font=F(26),
                                fill=(255, 205, 80, 230), anchor="ra")
        p = WORK / f"{b['ad']}_filigran.png"
        im.save(p)
        out.append((p, 0, d))
    kel = b["metin"].split()
    if not kel:
        return out
    parcalar, simdiki = [], []
    for k in kel:
        simdiki.append(k)
        if len(simdiki) >= 12 or (k.endswith((".", "!", "?", ":")) and len(simdiki) >= 5):
            parcalar.append(simdiki)
            simdiki = []
    if simdiki:
        parcalar.append(simdiki)
    t, birim = 0.2, (d - PAY) / len(kel)
    for j, p in enumerate(parcalar):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im, "RGBA")
        satirlar = sar(dr, " ".join(p), F(40, False), 1600)
        y0 = H - 60 - 52 * len(satirlar)
        dr.rectangle((0, y0 - 20, W, H), fill=(0, 0, 0, 150))
        for n, s in enumerate(satirlar):
            dr.text((W / 2, y0 + n * 52), s, font=F(40, False), fill=BEYAZ, anchor="ma")
        png = WORK / f"{b['ad']}_alt{j}.png"
        im.save(png)
        out.append((png, round(t, 2), round(t + birim * len(p), 2)))
        t += birim * len(p)
    return out


def bolum_videosu(b, d, altyazi, filigran):
    agirlik = sum(p[1] for p in b["planlar"])
    planlar = [plan_videosu(b, i, p, round(d * p[1] / agirlik, 3)) for i, p in enumerate(b["planlar"])]
    katmanlar = altyazi_katmanlari(b, d, filigran) if (altyazi or filigran) else []
    if not altyazi:
        katmanlar = [k for k in katmanlar if "filigran" in k[0].name]
    args, fc = [], []
    for p in planlar:
        args += ["-i", p]
    for k in katmanlar:
        args += ["-loop", 1, "-framerate", FPS, "-t", d, "-i", k[0]]
    n = len(planlar)
    fc.append("".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[c0]")
    son = "c0"
    for j, (_p, a, e) in enumerate(katmanlar):
        fc.append(f"[{son}][{n + j}:v]overlay=enable='between(t,{a},{e})'[c{j + 1}]")
        son = f"c{j + 1}"
    out = WORK / f"{b['ad']}.mp4"
    ff(*args, "-filter_complex", ";".join(fc), "-map", f"[{son}]", *ENC, "-t", d, out)
    return out


# ---------------------------------------------------------------- ses
def ses(zaman, toplam):
    args, fc, mix = [], [], []
    n = 0
    for b, (a, d) in zip(BOLUMLER, zaman):
        ms = int(a * 1000)
        if "film_sesi" in b:
            args += ["-ss", b["film_sesi"], "-t", d, "-i", FILM]
            fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.3,"
                      f"afade=t=out:st={d - 0.5}:d=0.5,adelay={ms}|{ms}[s{n}]")
        else:
            k = hazir_kayit(b["ad"])
            if not k:
                continue
            args += ["-i", k]
            # telefon kaydı: gürültü azaltma, sıkıştırma, seviye eşitleme
            fc.append(f"[{n}:a]aresample=48000,highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:"
                      f"attack=5:release=100,loudnorm=I=-16:TP=-2,aresample=48000,aformat=channel_layouts=stereo,"
                      f"adelay={ms}|{ms}[s{n}]")
        mix.append(f"[s{n}]")
        n += 1
    # müzik yatağı: konuşma altında kısık; film bölümünde susar
    a3, d3 = next(z for b, z in zip(BOLUMLER, zaman) if "film_sesi" in b)
    args += ["-stream_loop", -1, "-i", ROOT / "assets/ses/kutuphane/Heartwarming.mp3"]
    fc.append(f"[{n}:a]atrim=0:{toplam},asetpts=N/SR/TB,aresample=48000,aformat=channel_layouts=stereo,"
              f"volume=0.09,volume='if(between(t,{a3 - 0.3},{a3 + d3 + 0.3}),0,1)':eval=frame,"
              f"afade=t=in:d=1,afade=t=out:st={toplam - 3}:d=3[muzik]")
    mix.append("[muzik]")
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0,loudnorm=I=-14:TP=-1.5,aresample=48000[a]")
    out = WORK / "ses.wav"
    ff(*args, "-filter_complex", ";".join(fc), "-map", "[a]", "-t", toplam, out)
    return out


# ---------------------------------------------------------------- metin
def anlatim_metni():
    zaman = [sure(b) for b in BOLUMLER]
    md = ["# Tanıtım videosu · okunacak metin ve kayıt rehberi", "",
          "Mert, bu metni kendi sesinle okuyacaksın. Yüzün görünmeyecek, yalnızca sesin. Görüntüler hazır: "
          "kayıtlar gelince video sesinin uzunluğuna göre kendiliğinden ayarlanacak.", "",
          "## Nasıl kaydedilir?", "",
          "1. Telefonun ses kaydedicisini aç (iPhone: Sesli Notlar, Android: Ses Kaydedici).",
          "2. Sessiz bir oda seç; halı, perde ve koltuk olan bir oda yankıyı azaltır. Telefonu ağzından bir karış uzakta tut.",
          "3. **Her bölümü ayrı bir dosya olarak kaydet** ve dosyanın adını bölüm numarası yap: `t01`, `t02`, `t04` … `t13`. "
          "`t03` yok, orada filmin kendi sesi çalıyor.",
          "4. Kayda başlayınca 1 saniye bekle, sonra oku. Bitince 1 saniye daha bekle ve durdur.",
          "5. Acele etme, gülümseyerek ve normal konuşur gibi oku. Takılırsan o bölümü baştan kaydetmen yeterli.",
          "6. Metni birebir okumak zorunda değilsin; kendi cümlelerinle de söyleyebilirsin. Video senin kaydının uzunluğuna uyar.", "",
          "Dosyaları bana iletmek için: Google Drive'a bir klasör aç, kayıtları oraya yükle ve linkini gönder. "
          "Ya da GitHub'da `assets/ses/tanitim/` klasörüne yükle.", "",
          f"Tahmini toplam süre: **{sum(zaman):.0f} sn** (şart: 60–180 sn).", "",
          "## Metin", ""]
    t = 0.0
    for b, d in zip(BOLUMLER, zaman):
        md += [f"### {b['ad']} · {b['baslik']}  ({t:.0f}–{t + d:.0f}. sn)", ""]
        md += [f"> {b['metin']}" if b["metin"] else "_Kayıt yok: burada filmden 14 saniyelik bir bölüm sesiyle oynuyor._", ""]
        t += d
    md += ["## Şartlarla eşleşme", "",
           "| Şart | Bölüm |", "| --- | --- |",
           "| Filmin konusu ve filmden bir bölüm | t02, t03 |",
           "| Storyboard ve bir karenin sahneye dönüşmesi | t04, t05 |",
           "| Kullanılan araçlar | t06 (ekranda model adları da yazıyor) |",
           "| En az 2 görsel prompt | t07 (Damla karakter kartı), t08 (toplama sahnesi) |",
           "| En az 2 video prompt | t09 (toplama klibi), t10 (yaprak klibi) |",
           "| Üretim kayıtları ve sonuçları | t07–t10 (sonuçlar), t11 (kayıtlar, kaynak listesi) |",
           "| Görsellerin ve videoların filmdeki yerleri | t05, t12 |", "",
           "## Son adım", "",
           "Final video `out/tanitim/TalentCup-2026_Son_Damla_Tanitim.mp4` olarak çıkacak. Onu Google Drive'a yükle, "
           "paylaşımı **Bağlantıya sahip olan herkes · Görüntüleyen** yap ve linki yarışmaya gönder.", ""]
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / "anlatim_metni.md").write_text("\n".join(md), encoding="utf-8")
    return OUTD / "anlatim_metni.md"


def main():
    if sys.argv[1:2] == ["metin"]:
        print(anlatim_metni().relative_to(ROOT))
        return
    WORK.mkdir(parents=True, exist_ok=True)
    OUTD.mkdir(parents=True, exist_ok=True)
    anlatim_metni()
    kayitli = [b["ad"] for b in BOLUMLER if b["metin"] and kayit_dosyasi(b["ad"])]
    eksik = [b["ad"] for b in BOLUMLER if b["metin"] and not kayit_dosyasi(b["ad"])]
    final = not eksik
    if kayitli and eksik:
        print("UYARI: eksik kayıtlar:", ", ".join(eksik), "→ önizleme üretiliyor")
    zaman, t = [], 0.0
    for b in BOLUMLER:
        d = sure(b)
        zaman.append((t, d))
        t += d
    toplam = round(t, 2)
    bolumler = [bolum_videosu(b, d, altyazi=(not final) or "--altyazi" in sys.argv, filigran=not final)
                for b, (_a, d) in zip(BOLUMLER, zaman)]
    liste = WORK / "liste.txt"
    liste.write_text("".join(f"file '{p.name}'\n" for p in bolumler), encoding="utf-8")
    video = WORK / "video.mp4"
    ff("-f", "concat", "-safe", 0, "-i", liste, "-c", "copy", video)
    sesdosya = ses(zaman, toplam)
    out = OUTD / ("TalentCup-2026_Son_Damla_Tanitim.mp4" if final else "tanitim_onizleme.mp4")
    ff("-i", video, "-i", sesdosya, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart", "-t", toplam, out)
    print(f"{out.relative_to(ROOT)}: {M.dur(out):.1f} sn", "(final)" if final else "(önizleme)")
    for b, (a, d) in zip(BOLUMLER, zaman):
        print(f"  {b['ad']} {a:6.1f}–{a + d:6.1f}  {b['baslik']}")


if __name__ == "__main__":
    main()
