# Rüzgârın Adları — Yaşayan Sözlük

Proje brifi: [`BRIEF.md`](BRIEF.md). Tek veri kaynağı: `data/maddeler.csv` (G1, BRIEF.md'den üretilir).

## Durum (28 Ekim 2026)

| Görev | Çıktı | Durum |
| --- | --- | --- |
| G1 Veri | `data/maddeler.csv` | ✓ 39 satır, benzersiz id, boş zorunlu alan yok |
| G2 Kayıt kiti | `print/seslendirme_metinleri.pdf` | ✓ talimat + 10 sayfa (sayfa başına 4 metin) |
| G3 Kart rehberleri | `print/kart_rehberleri.pdf` | ✓ 39 rehber + 4 boş kesim şablonu (yalnızca yol gösterici) |
| G4 Taban şablonu | `print/taban_ruzgar_gulu.pdf` | ✓ 1:5 genel görünüş + 8 adet 1:1 A4 sayfa |
| G5 Duvar planları | `print/yerlesim_planlari.pdf` | ✓ 1:5; arka duvar kartları küçültüldü (aşağıda) |
| G6 Videolar | `videos/NN_slug.mp4` | betik hazır, örnek veriyle test edildi; fotoğraf ve ses bekleniyor |
| G7 Döngü | `videos/tum_videolar_dongu.mp4` | betik hazır, test edildi |
| G8 Yükleme listesi | `uploads/youtube_listesi.csv`, `data/links.csv` şablonu | betik hazır; `links.csv` boş şablon oluşturuldu |
| G9 QR | `print/qr_etiketleri.pdf` | betik hazır, test edildi (geri okuma PNG + basılacak PDF üzerinden) |
| G10 Dizin | `print/dizin_rehberi.pdf` | ✓ Türk alfabesine göre, satır/sıra bilgisiyle |
| G11 Yedek promptlar | `data/higgsfield_promptlari.txt` | ✓ 39 prompt |

### Kart boyutu değişikliği (G5 raporu)

Arka duvar 60 cm; 2 cm kenar boşlukları düşülünce 56 cm kalıyor.

- Arka üst (12–21, 5×2): 5 × 11 + 4 × 1,5 = 61 cm gerekiyor → **10×12,7 cm**
- Arka alt (22–27, tek sıra 6): 6 × 9 + 5 × 1,5 = 61,5 cm gerekiyor → **8×10,6 cm**

Diğer kart boyutları değişmedi. `maddeler.csv`, kart rehberleri ve planlar yeni ölçüleri kullanıyor.
Alternatif: alt bölüm 3+3 dizilirse 9×12 cm korunabilir; yükseklik yeterli. Bu durumda
`scripts/yerlesim.py` içindeki `DUVAR_BOLUMLERI` değiştirilir.

### Taban yerleşimi

K (Yıldız) arka duvar tarafındadır. Köşelerde: 09 Rüzgâr gülü (arka sol), 10 Orsa (arka sağ),
11 Pupa (ön sol). Proje adı ön sağ köşededir. Pusula yuvası varsayılan olarak Ø 5 cm'dir; farklı bir
pusula için `python3 scripts/g04_taban.py --pusula 6` çalıştırılır.

## Çalıştırma

```bash
pip install -r requirements.txt     # ffmpeg ve poppler-utils (pdftoppm) da gerekir
./scripts/hazirlik.sh               # G1–G5, G10, G11 + links.csv şablonu + kontrol
python3 scripts/g06_videolar.py     # 7 Kasım: media/images/NN.jpg + media/audio/NN.m4a gerekir
python3 scripts/g07_dongu.py
python3 scripts/g08_yukleme_listesi.py
python3 scripts/g09_qr.py           # 8–9 Kasım: data/links.csv dolu olmalı
python3 scripts/kontrol.py          # kabul kriterleri
```

Bütün betikler `data/maddeler.csv` dosyasını okur. Bir madde değişecekse önce `BRIEF.md` düzeltilir,
sonra `hazirlik.sh` yeniden çalıştırılır.

## Notlar

- **Kural 1:** Kart yüzleri basılmaz. Kart rehberlerinin her kartında "REHBER · YAPIŞTIRMA" filigranı
  vardır. Yalnızca QR etiketleri basılıp yapıştırılır.
- **Kural 5:** Doğrulanmamış köken ve anlamlar (BRIEF bölüm 8) rehberlerde kırmızı "doğrula" uyarısıyla
  işaretlidir. Listesi rehber PDF'inin ilk sayfasındadır.
- G6 altyazıları en çok 7 kelimelik parçalara bölünür. Parçalar ses süresine uzunluklarıyla orantılı
  dağıtılır. Ses 0,5. saniyede başlar; son 1 saniyede "Rüzgârın Adları · Yaşayan Sözlük" görünür.
- Öğrencinin ses kayıtları ve fotoğrafları (`media/`) ile videolar (`videos/*.mp4`) gizlilik ve
  depo boyutu nedeniyle git'e eklenmez (`.gitignore`).
- Font: sistemde Noto Sans varsa o, yoksa DejaVu Sans kullanılır. İkisi de Türkçe karakterleri ve
  eski metinlerdeki ŋ, ó gibi harfleri kapsar. `kontrol.py` bunu doğrular.
