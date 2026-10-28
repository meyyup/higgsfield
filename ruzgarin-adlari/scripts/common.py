"""Rüzgârın Adları — ortak yardımcılar.

Bütün betikler veriyi data/maddeler.csv'den okur (G1 bunu BRIEF.md'den üretir).
Ölçüler santimetre cinsindendir.
"""
import csv
import math
import os
import re
import unicodedata

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# RUZGAR_KOK ortam değişkeni, betikleri başka bir klasörde (ör. test) çalıştırmak içindir.
ROOT = os.environ.get("RUZGAR_KOK") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PRINT = os.path.join(ROOT, "print")
MEDIA = os.path.join(ROOT, "media")
VIDEOS = os.path.join(ROOT, "videos")
UPLOADS = os.path.join(ROOT, "uploads")
CSV_PATH = os.path.join(DATA, "maddeler.csv")

PROJE_ADI = "Rüzgârın Adları"
ALT_BASLIK = "Yaşayan Sözlük"
STIL = ("Vertical 9:16, soft watercolor children's book illustration, "
        "warm colors, no text, no logos.")

# --- Font: Türkçe karakterleri (ç ğ ı İ ö ş ü â î û) eksiksiz taşıyan font ---
FONT_ADAYLARI = [
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
     "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
for _r, _b in FONT_ADAYLARI:
    if os.path.exists(_r) and os.path.exists(_b):
        FONT_REGULAR_PATH, FONT_BOLD_PATH = _r, _b
        break
else:
    raise SystemExit("Türkçe destekli font bulunamadı (Noto Sans ya da DejaVu Sans kurun).")

F = "Govde"
FB = "GovdeKalin"
pdfmetrics.registerFont(TTFont(F, FONT_REGULAR_PATH))
pdfmetrics.registerFont(TTFont(FB, FONT_BOLD_PATH))

TURKCE_TEST = "çÇğĞıIİiöÖşŞüÜâÂîûó"


def font_kapsami_kontrol(metin):
    """Fontta karşılığı olmayan karakterleri döndürür."""
    face = pdfmetrics.getFont(F).face
    eksik = sorted({ch for ch in metin if not ch.isspace() and ord(ch) not in face.charToGlyph})
    return eksik


# --- Konumlar ve kart boyutları -------------------------------------------
YONLER = {
    "K": "kuzey", "KD": "kuzeydoğu", "D": "doğu", "GD": "güneydoğu",
    "G": "güney", "GB": "güneybatı", "B": "batı", "KB": "kuzeybatı",
}

# Bölüm 2'deki özgün kart boyutları (genişlik, yükseklik)
KART_BOYUTU_BRIF = {
    "TABAN": (9.0, 12.0),
    "ARKA-UST": (11.0, 14.0),
    "ARKA-ALT": (9.0, 12.0),
    "SOL": (12.0, 16.0),
    "SAG": (9.0, 12.0),
}

# Duvarlar (genişlik, yükseklik) ve yerleşim kuralları
DUVARLAR = {"ARKA": (60.0, 65.0), "SOL": (50.0, 65.0), "SAG": (50.0, 65.0)}
TABAN = (60.0, 50.0)
KENAR = 2.0        # en az kenar boşluğu
ARALIK = 1.5       # kartlar arası en az boşluk
BASLIK_YUK = 3.0   # duvar başlık alanı yüksekliği


def bolge(konum):
    return "TABAN" if konum.startswith("TABAN") else konum


def sigdir(boyut, adet, alan):
    """`adet` kart bir sıraya `alan` genişliğe sığmıyorsa orantılı küçült.

    Genişlik 0,5 cm'ye aşağı yuvarlanır, yükseklik orantılı (0,1 cm)."""
    w, h = boyut
    gerek = adet * w + (adet - 1) * ARALIK
    if gerek <= alan:
        return boyut
    yeni_w = math.floor(((alan - (adet - 1) * ARALIK) / adet) * 2) / 2
    yeni_h = math.floor(h * yeni_w / w * 10) / 10
    return (yeni_w, yeni_h)


def _kart_boyutlari():
    b = dict(KART_BOYUTU_BRIF)
    ic_arka = DUVARLAR["ARKA"][0] - 2 * KENAR
    ic_yan = DUVARLAR["SOL"][0] - 2 * KENAR
    b["ARKA-UST"] = sigdir(b["ARKA-UST"], 5, ic_arka)
    b["ARKA-ALT"] = sigdir(b["ARKA-ALT"], 6, ic_arka)
    b["SOL"] = sigdir(b["SOL"], 3, ic_yan)
    b["SAG"] = sigdir(b["SAG"], 4, ic_yan)
    return b


KART_BOYUTU = _kart_boyutlari()


def kart_boyutu(konum):
    return KART_BOYUTU[bolge(konum)]


def boyut_yazi(b):
    return f"{fmt(b[0])}×{fmt(b[1])}"


def boyut_oku(s):
    w, h = s.replace(",", ".").split("×")
    return float(w), float(h)


def fmt(x):
    """Türkçe ondalık: 12.7 -> '12,7', 9.0 -> '9'."""
    x = round(x, 2)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.1f}".replace(".", ",")


# --- Slug ve sıralama ---------------------------------------------------------
_ASCII = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                        "â": "a", "î": "i", "û": "u"})


def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


def slugla(id_, madde):
    s = tr_lower(madde).translate(_ASCII)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return f"{id_}_{s}"


ALFABE = "abcçdefgğhıijklmnoöprsştuüvyz"
_ESDEGER = {"â": "a", "î": "i", "û": "u"}


def tr_sirala_anahtar(s):
    anahtar = []
    for ch in tr_lower(s):
        ch = _ESDEGER.get(ch, ch)
        if ch in ALFABE:
            anahtar.append(ALFABE.index(ch) + 1)
        elif ch.isspace():
            anahtar.append(0)
        # noktalama sıralamada yok sayılır
    return anahtar


# --- Okunur konum -------------------------------------------------------------
def okunur_konum(konum):
    if konum.startswith("TABAN-"):
        kod = konum.split("-", 1)[1]
        if kod == "KOSE":
            return "Taban, köşe"
        return f"Taban, {YONLER[kod]}"
    return {
        "ARKA-UST": "Arka duvar, üst bölüm (Rüzgârın adları)",
        "ARKA-ALT": "Arka duvar, alt bölüm (Dilimizde rüzgâr)",
        "SOL": "Sol duvar (1000 yıl önce)",
        "SAG": "Sağ duvar (Rüzgâr ve zanaat)",
    }[konum]


# --- Köken doğrulaması (BRIEF bölüm 8) ---------------------------------------
# Kural 5: doğrulanmadan karta yazılmaz. Rehberlerde uyarı olarak basılır.
DOGRULANACAK = {
    "02": "Boreas bağlantısı (Nişanyan/TDK)",
    "16": "Boreas bağlantısı (Nişanyan/TDK)",
    "04": "Keşiş Dağı (Uludağ) açıklaması",
    "14": "\"embates\" kökeni",
    "15": "\"semûm\" kökeni",
    "17": "\"fortuna\" kökeni",
    "19": "\"hurtum\" kökeni",
    "10": "İtalyanca kökeni",
    "11": "İtalyanca kökeni",
    "32": "Kutadgu Bilig beyit numarası (65 ya da 69)",
    "22": "Anlam: TDK Atasözleri ve Deyimler Sözlüğü",
    "23": "Anlam: TDK Atasözleri ve Deyimler Sözlüğü",
    "24": "Anlam: TDK Atasözleri ve Deyimler Sözlüğü",
    "25": "Anlam: TDK Atasözleri ve Deyimler Sözlüğü (özellikle)",
    "26": "Anlam: TDK Atasözleri ve Deyimler Sözlüğü",
    "27": "Anlam: TDK Atasözleri ve Deyimler Sözlüğü",
}


# --- CSV ----------------------------------------------------------------------
SUTUNLAR = ["id", "slug", "madde", "tur", "konum", "kart_boyutu", "cumle", "koken",
            "alinti", "cizim", "seslendirme", "prompt"]


def maddeleri_oku():
    if not os.path.exists(CSV_PATH):
        raise SystemExit("data/maddeler.csv yok; önce scripts/g01_veri.py çalıştırın.")
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# --- PDF sayfa çerçevesi --------------------------------------------------------
BASKI_NOTU = "%100 ölçekte basın, sayfaya sığdırmayın"
GRI = (0.55, 0.55, 0.55)
ACIK_GRI = (0.72, 0.72, 0.72)


def sayfa_cercevesi(c, sayfa_boyu, baslik, sayfa_no=None, kontrol_x=None):
    """Her sayfaya: üstte başlık + baskı notu, altta 5 cm'lik kontrol çizgisi."""
    W, H = sayfa_boyu
    c.saveState()
    c.setFillColorRGB(0.25, 0.25, 0.25)
    c.setFont(F, 8)
    c.drawRightString(W - 0.8 * cm, H - 0.6 * cm, BASKI_NOTU)
    # Başlık, baskı notuyla çakışmayacak puntoya küçültülür
    yer = W - 1.6 * cm - pdfmetrics.stringWidth(BASKI_NOTU, F, 8) - 0.6 * cm
    punto = 9.0
    while pdfmetrics.stringWidth(baslik, FB, punto) > yer and punto > 6:
        punto -= 0.5
    c.setFont(FB, punto)
    c.drawString(0.8 * cm, H - 0.6 * cm, baslik)
    # 5 cm kontrol çizgisi
    x0 = (kontrol_x if kontrol_x is not None else 0.8) * cm
    y0 = 0.55 * cm
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.line(x0, y0, x0 + 5 * cm, y0)
    for i in range(6):
        t = 0.25 * cm if i in (0, 5) else 0.12 * cm
        c.line(x0 + i * cm, y0, x0 + i * cm, y0 + t)
    c.setFont(F, 7)
    c.drawString(x0 + 5.2 * cm, y0 - 0.05 * cm, "5 cm kontrol çizgisi — cetvelle ölçün")
    if sayfa_no is not None:
        c.drawRightString(W - 0.8 * cm, y0 - 0.05 * cm, f"Sayfa {sayfa_no}")
    c.restoreState()


def satir_kir(metin, font, boyut, genislik_pt):
    """Basit kelime kaydırma; genislik_pt sabit ya da satır no -> genişlik fonksiyonu."""
    kelimeler = metin.split()
    satirlar, mevcut = [], ""
    for k in kelimeler:
        g = genislik_pt(len(satirlar)) if callable(genislik_pt) else genislik_pt
        aday = f"{mevcut} {k}".strip()
        if pdfmetrics.stringWidth(aday, font, boyut) <= g or not mevcut:
            mevcut = aday
        else:
            satirlar.append(mevcut)
            mevcut = k
    if mevcut:
        satirlar.append(mevcut)
    return satirlar


def pil_font(boyut, kalin=False):
    from PIL import ImageFont
    return ImageFont.truetype(FONT_BOLD_PATH if kalin else FONT_REGULAR_PATH, boyut)


A4P = A4
A4L = landscape(A4)
