"""Taban ve duvar yerleşimleri (cm, orijin sol üst köşe, y aşağı).

G4 (taban şablonu), G5 (duvar planları) ve G10 (dizin) aynı yerleşimi kullanır.
"""
import math

from common import ARALIK, BASLIK_YUK, DUVARLAR, KENAR, TABAN, kart_boyutu

# --- Taban -------------------------------------------------------------------
# Kuzey (K) arka duvar tarafındadır; önden bakan ziyaretçi için doğu sağdadır.
TABAN_MERKEZ = (TABAN[0] / 2, TABAN[1] / 2)
# Kart sol üst köşeleri (9×12 dikey kart için)
TABAN_KARTLARI = {
    "TABAN-K": (25.5, 2.0), "TABAN-KD": (38.5, 7.0), "TABAN-D": (49.0, 19.0),
    "TABAN-GD": (38.5, 31.0), "TABAN-G": (25.5, 36.0), "TABAN-GB": (12.5, 31.0),
    "TABAN-B": (2.0, 19.0), "TABAN-KB": (12.5, 7.0),
}
TABAN_KOSELER = [(2.0, 2.0), (49.0, 2.0), (2.0, 36.0)]   # 09, 10, 11 (sırayla)
PROJE_ADI_KOSESI = (49.0, 36.0)                          # 4. köşe: proje adı


def taban_yerlesimi(rows):
    """[(row|None, x, y, w, h, etiket)] — etiket: yön kodu, 'KÖŞE' ya da 'PROJE'."""
    w, h = kart_boyutu("TABAN-K")
    out = []
    koseler = iter(TABAN_KOSELER)
    for r in rows:
        k = r["konum"]
        if k == "TABAN-KOSE":
            x, y = next(koseler)
            out.append((r, x, y, w, h, "KÖŞE"))
        elif k.startswith("TABAN-"):
            x, y = TABAN_KARTLARI[k]
            out.append((r, x, y, w, h, k.split("-")[1]))
    out.append((None, *PROJE_ADI_KOSESI, w, h, "PROJE"))
    return out


# --- Duvarlar ----------------------------------------------------------------
DUVAR_BOLUMLERI = {
    "ARKA": [("Rüzgârın adları", "ARKA-UST", [5, 5]), ("Dilimizde rüzgâr", "ARKA-ALT", [6])],
    "SOL": [("1000 yıl önce", "SOL", [3, 2])],
    "SAG": [("Rüzgâr ve zanaat", "SAG", [4, 3])],
}
BOLUM_ARASI = 2.5
DIZIN_ALANI = (14.8, 21.0)  # A5 dikey; sağ duvarda isteğe bağlı dizin kartı yeri


def _yuvarla(x):
    return round(x * 10) / 10


def duvar_yerlesimi(duvar, rows):
    """Döndürür: {'kartlar': [(row, x, y, w, h, satir, sira)], 'basliklar': [(metin, x, y, w, h)],
    'dizin': (x, y, w, h) | None}. İçerik duvarda dikeyde ortalanır."""
    W, H = DUVARLAR[duvar]
    ic = W - 2 * KENAR
    kartlar, basliklar = [], []
    y = 0.0
    for bi, (baslik, konum, satirlar) in enumerate(DUVAR_BOLUMLERI[duvar]):
        if bi:
            y += BOLUM_ARASI
        basliklar.append((baslik, KENAR, y, ic, BASLIK_YUK))
        y += BASLIK_YUK + ARALIK
        grup = [r for r in rows if r["konum"] == konum]
        w, h = kart_boyutu(konum)
        i = 0
        for si, n in enumerate(satirlar):
            if si:
                y += ARALIK
            n_max = max(satirlar)
            # Aynı bölümdeki satırlar aynı aralığı kullanır (sütunlar hizalı kalsın)
            bosluk = (ic - n_max * w) / (n_max - 1) if n_max > 1 else 0
            bosluk = max(ARALIK, min(3.0, math.floor(bosluk * 2) / 2))
            toplam = n * w + (n - 1) * bosluk
            x0 = math.floor((W - toplam) / 2 * 10) / 10
            for j in range(n):
                kartlar.append((grup[i], _yuvarla(x0 + j * (w + bosluk)), y, w, h, si + 1, j + 1))
                i += 1
            y += h
        assert i == len(grup), f"{konum}: {len(grup)} kart, yerleşim {sum(satirlar)}"
    dizin = None
    if duvar == "SAG":
        y += BOLUM_ARASI
        dizin = ((W - DIZIN_ALANI[0]) / 2, y, *DIZIN_ALANI)
        y += DIZIN_ALANI[1]
    # Dikeyde ortala
    kaydir = _yuvarla(max(KENAR, (H - y) / 2))
    kartlar = [(r, x, _yuvarla(yy + kaydir), w, h, s, j) for r, x, yy, w, h, s, j in kartlar]
    basliklar = [(m, x, _yuvarla(yy + kaydir), w, h) for m, x, yy, w, h in basliklar]
    if dizin:
        dizin = (_yuvarla(dizin[0]), _yuvarla(dizin[1] + kaydir), dizin[2], dizin[3])
    return {"kartlar": kartlar, "basliklar": basliklar, "dizin": dizin}


# --- Denetim -------------------------------------------------------------------
def kutular_denetle(ad, alan, kutular, kenar=KENAR, aralik=ARALIK):
    """Kenar boşluğu ve kartlar arası en az boşluğu denetler; hata listesi döndürür."""
    W, H = alan
    hatalar = []
    eps = 1e-6
    for etiket, x, y, w, h in kutular:
        if x < kenar - eps or y < kenar - eps or x + w > W - kenar + eps or y + h > H - kenar + eps:
            hatalar.append(f"{ad}: {etiket} kenar boşluğu {kenar} cm'den az")
    for i, (e1, x1, y1, w1, h1) in enumerate(kutular):
        for e2, x2, y2, w2, h2 in kutular[i + 1:]:
            dx = max(x2 - (x1 + w1), x1 - (x2 + w2))
            dy = max(y2 - (y1 + h1), y1 - (y2 + h2))
            if max(dx, dy) < aralik - eps:
                hatalar.append(f"{ad}: {e1} ile {e2} arası {max(dx, dy):.1f} cm (< {aralik})")
    return hatalar
