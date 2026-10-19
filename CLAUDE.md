# ±1°C – Bir Derece · Claude Code Üretim ve Montaj Brifi

Bu dosyayı proje kökünde `CLAUDE.md` olarak kullan. Görev: aşağıdaki konsepti baştan sona sen tasarla, prompt'ları yaz,
Higgsfield API ile üret, montajla ve teslim paketini çıkar. Dış referans yok; ihtiyacın olan her şey bu dosyada.

## 0. Yetki ve sınırlar

- AI görsel/video üretirsin. Higgsfield API'sine istek atarsın (`HIGGSFIELD_API_KEY` ortam değişkeni; başlamadan API dokümantasyonunu ve kredi bakiyesini kontrol et, yetmeyecekse DUR).
- Prompt'ları sen yazarsın. Her prompt'u `prompts/<dosya_adi>.txt` olarak kaydet.
- Her API çağrısını `out/uretim_logu/<dosya_adi>.json` olarak logla: zaman, model, prompt birebir, parametreler, dönen ID/URL, kaydedilen dosya.
- Her görsel için 2 aday üret; kabul ölçütüne göre birini seç, diğerini `out/adaylar/` altında sakla. Yalnızca iki noktada kullanıcıya sor (DUR): kadraj referansı ve Ela referansı.
- Ses: iki konuşma cümlesi için `assets/ses/ses_k1.m4a` ve `ses_k3.m4a` bekle; yoksa DUR ve kaydedilmesini iste. Müzik ve efektleri telifsiz kütüphaneden al, kaynağını yaz.
- Marka, logo, yaprak simgesi, tanınabilir ürün tasarımı kullanma. Termostat özgün: yuvarlak metal çerçeve, siyah ekran, büyük beyaz rakam.
- Metinlerdeki Türkçe karakterleri her çıktıda test et.

## 1. Konsept

- Film adı (ekranda): **±1°C**. YouTube başlığı: **TalentCup-2026 Bir Derece**.
- Mesaj: Kışın kombiyi 1 derece kıs, yazın klimayı 1 derece aç. Küresel ısınmanın "1 derecesi" ile evdeki "1 derece" aynı kadrajda.
- Kapanış (değiştirme):
  1. Büyük değişiklikler küçük hareketlerle başlar.
  2. İleriyi düşün. Sen de 1 derece katkı ver.
  3. (küçük punto) Kışın kombiyi 1 derece kıs, yazın klimayı 1 derece aç.
- Kahraman: **Ela**, 12 yaşında kız. Anlatıcı yok; yalnızca iki fısıltı cümlesi.
- Mekanik: duvarda yuvarlak termostat, hemen sağında pencere. Çevirmek = derece. Gözlerini kapamak = zaman Ela'nın kafasında ileri akar (hayal). Tek gerçek "klik" K5'te.
- Süre: 60 sn; izin verilen aralık 55–65. 6 sahne.

## 2. Hikâye

Kış gecesi. Ela üşüyor. Termostat 23; çevirir: 24. "Bir derece, kimse fark etmez." Bastıracakken pencereye takılır: tepede
kar yok. Gözlerini kapar; kafasında pencere ileri akar: 2030 karsız tepe, 2040 dedesinin ağacı kurumuş, 2055 deniz
kıyıya tırmanmış, 2076 turuncu gök, boş sokak. Gözlerini açar: termostat 24, pencere 2026; hiçbir şey olmamış, ama o
görmüş. İki tık geri: 22. Yine gözlerini kapar: 2030 kar duruyor, 2040 ağaç büyümüş, 2055 gölgesi pencereye uzanıyor,
2076 ağacın altında yaşlı bir kadın pencereye bakıyor. Gözlerini açar, bastırır: klik. Kazağını giyer. Yaz: aynı
termostat mavi modda 24; gözlerini kapamadan +1: 25. Artık biliyor.

## 3. Görsel dil

- Tek sabit kadraj: koridor duvarı, solda yuvarlak termostat, sağında pencere; pencerede tepe, bir ağaç, uzakta deniz. Kamera sabit, göz hizası, karşıdan.
- Gözler kapalı = hayal: hafif vignette, doygunluk ~0,7, kenar bulanıklığı. Gözler açık = gerçek: keskin, normal renk. Filtre montajda uygulanır, üretimde değil.
- Stil cümlesi (her prompt'un sonunda aynen): `prompts/stil.txt` varsa oradan; yoksa "sinematik, gerçekçi, sıcak renkler, yumuşak ışık".
- Ela: kazak rengi bir kez seçilir ve her karede aynı. Yüz yalnızca gözler karesinde görünür.

## 4. Storyboard ve zaman çizelgesi

| Sn | Kare | Görüntü | Ses | Ekran yazısı |
| --- | --- | --- | --- | --- |
| 0–6 | K1 | klip5 (parmak termostatı 23→24 çeviriyor), son karede 1 sn donma | ses_k1 (fısıltı: "Bir derece, kimse fark etmez.") + çevirme tıkırtısı | 0–3 sn: "±1°C" büyük, altında "BİR DERECE"; 3–6 sn: "Ben Ela." |
| 6–20 | K2 | klip6 (gözler kapanıyor, 2 sn) → klip1 (2026→2040 kötü) → pencere_kotu_2055 sabit 1 sn → klip2 (2040→2076 kötü); hayal filtresi; yıl sayacı | müzik hızlanan; rüzgâr | Yıl sayacı 2026→2076 sağ üst; 14–20 sn: "Dünya yaklaşık 1 derece ısındı." |
| 20–28 | K3 | klip6 ters (gözler açılıyor, 2 sn) → klip5 ters iki adım (24→23→22) | ses_k3 ("Hiçbir şey olmamıştı. Sadece ben görmüştüm.") + iki tıkırtı; müzik durur | "–2" |
| 28–42 | K4 | klip6 (2 sn) → klip3 (2026→2040 iyi) → pencere_iyi_2055 sabit 1 sn → klip4 (2040→2076 iyi); hayal filtresi; yıl sayacı | müzik yumuşak, açılan | Yıl sayacı |
| 42–54 | K5 | klip6 ters (2 sn) → 1 sn sessiz sabit kare → klik → termostat "22" sabit 4 sn → termostat_yaz_25 sabit 3 sn | klik.wav tek; müzik sıcak | "–1 kış" · "+1 yaz" |
| 54–60 | K6 | termostat "22" sabit kare, pencereye kar efekti (ffmpeg partikül) | müzik fade-out | Kapanış 3 satır + "TalentCup-2026" |

Klip süreleri uymazsa `setpts` ile en fazla ±%20 oynat; daha fazlası gerekirse kırp.

## 5. Üretilecek varlıklar ve prompt içeriği

Dosya adlarını aynen kullan. "İçerik" sütunu prompt'un çekirdeği; başına sabit kadraj tarifi (§3), sonuna stil cümlesi gelir. Rakamlar prompt'ta açıkça yazılır.

### 5.1 Görseller (16:9, 2 aday)

| Dosya | İçerik | Referans | Kabul ölçütü |
| --- | --- | --- | --- |
| kadraj_ref.png | Koridor duvarı, gece; yuvarlak termostat ekranda "23"; sağında pencere; pencerede tepe, çıplak ağaç, uzakta deniz; karsız kış; loş koridor, pencereden mavi gece ışığı | — | 23 okunuyor; termostat ve pencere aynı duvarda; tepe/ağaç/deniz ayırt ediliyor. **DUR: kullanıcı seçsin** |
| pencere_kotu_2026.png | = kadraj_ref, termostat "24" | kadraj_ref | yalnızca rakam değişmiş |
| pencere_kotu_2030.png | Tepe kahverengi, kar yok; termostat 24 | kadraj_ref | duvar/termostat aynı |
| pencere_kotu_2040.png | Ağaç kurumuş, toprak çatlak; 24 | kadraj_ref | aynı |
| pencere_kotu_2055.png | Deniz kıyıya tırmanmış, sokak su altında; 24 | kadraj_ref | aynı |
| pencere_kotu_2076.png | Turuncu gök, boş sokak, cam buğulu, ağaç yok; 24 | kadraj_ref | aynı |
| pencere_iyi_2030.png | Tepede kar duruyor; termostat "22" | kadraj_ref | aynı |
| pencere_iyi_2040.png | Ağaç büyümüş, yapraklı; 22 | kadraj_ref | aynı |
| pencere_iyi_2055.png | Ağacın gölgesi pencereye uzanıyor, deniz yerinde; 22 | kadraj_ref | aynı |
| pencere_iyi_2076.png | Ağacın altında yaşlı bir kadın pencereye bakıyor, mavi gök; 22 | kadraj_ref | aynı |
| ela_ref.png | 12 yaşında kız, kazak, loş koridor, yüz yakın plan | — | **DUR: kullanıcı seçsin** |
| ela_el_24.png | Çocuk eli termostatı çeviriyor, ekranda "24", parmak düğmede | ela_ref + kadraj_ref | 24 okunuyor, kazak aynı |
| ela_gozler_kapali.png | Ela yakın plan, gözler kapalı, yüzde pencereden mavi ışık | ela_ref | aynı kız |
| ela_gozler_acik.png | Aynı kadraj, gözler açık, kararlı bakış | ela_ref | aynı kadraj |
| termostat_yaz_25.png | Aynı termostat, mavi ekran "25", gündüz ışığı, pencerede yaz | kadraj_ref | 25 okunuyor |

### 5.2 Videolar (720p, 16:9, ses kapalı)

| Dosya | Başlangıç karesi | Bitiş karesi | Model | Süre | Hareket tarifi (prompt) |
| --- | --- | --- | --- | --- | --- |
| klip1_kotu_sarma_A.mp4 | pencere_kotu_2026 | pencere_kotu_2040 | Seedance 2.0 (kredi kısıtlıysa 2.0 Mini) | 6–8 sn | pencere manzarası yavaşça değişiyor, kamera sabit, duvar ve termostat hareketsiz |
| klip2_kotu_sarma_B.mp4 | pencere_kotu_2040 | pencere_kotu_2076 | Seedance 2.0 | 6–8 sn | aynı |
| klip3_iyi_sarma_A.mp4 | pencere_kotu_2026 | pencere_iyi_2040 | Seedance 2.0 | 6–8 sn | aynı |
| klip4_iyi_sarma_B.mp4 | pencere_iyi_2040 | pencere_iyi_2076 | Seedance 2.0 | 6–8 sn | aynı |
| klip5_termostat_cevirme.mp4 | ela_el_24 | — | Seedance 1.5 Pro | 4–5 sn | parmak düğmeyi saat yönünde çeviriyor, rakam 23'ten 24'e, kamera sabit |
| klip6_gozler.mp4 | ela_gozler_acik | ela_gozler_kapali | Seedance 1.5 Pro | 4 sn | gözler yavaşça kapanıyor, yüz sabit, kamera sabit |

Genre: drama. Speed-ramp: linear. Kabul: sarmalarda duvar ve termostat kıpırdamıyor; çevirmede rakam okunuyor; gözler klibinde yüz değişmiyor. Kabul edilmeyen klip en fazla 2 kez yeniden üretilir, sonra DUR.

## 6. Üretim sırası

1. Kredi ve API kontrolü.
2. kadraj_ref → 2 aday → **DUR**, kullanıcı seçer.
3. 9 pencere görseli (kadraj_ref referanslı).
4. ela_ref → 2 aday → **DUR**.
5. ela_el_24, ela_gozler_kapali, ela_gozler_acik, termostat_yaz_25.
6. klip1–6.
7. Montaj (§7).
8. Teslim paketi (§8).

Her adımdan sonra kısa rapor: üretilen, seçilen, reddedilen, harcanan kredi.

## 7. Montaj

- Araç: ffmpeg + PIL. Scriptler `scripts/` altında (`generate.py`, `normalize.py`, `overlays.py`, `assemble.sh`, `check.py`), tekrar çalıştırılabilir.
- Normalize: 1920×1080, 25 fps, sessiz; oran farkı merkezden kırpılır.
- Yazı: Türkçe destekli font (DejaVu Sans / Inter), beyaz, hafif gölge; yazı kartları alt üçte bir, yıl sayacı sağ üst. PIL ile şeffaf PNG, ffmpeg overlay.
- Hayal filtresi §3'teki gibi; yalnızca K2 ve K4 sarma bölümlerine.
- Ses: ses_k1 ve ses_k3 orijinal seviye; müzik konuşma altında −12 dB; müzik 6–20 sn ve 28–60 sn (fade); klik 42. sn, öncesinde 1 sn tam sessizlik; toplam müzik ≥ 10 sn.
- Altyazı: `out/altyazi.srt` (K1: 0,5–3,5 sn; K3: 21–26 sn), videoya göm ve ayrıca ver.
- Çıktı: `out/TalentCup-2026_Bir_Derece_final.mp4`, H.264 + AAC, ~−14 LUFS. Süre 55–65 sn dışındaysa DUR.

## 8. Kontrol ve teslim

- `out/kontrol.md`: film adı ilk 5 sn · "Ben Ela." yazılı · sorun gösterildi (K2) ve söylendi (K1 ses, K2 yazı) · çözüm (K5 klik) · ne değişti (K4, K6) · ≥4 sahne · ≥2 sn hareket · sesli tam cümle altyazılı · müzik ≥10 sn · kapanış davranışı · süre. Her madde için geçti/kaldı + saniye.
- `out/kaynak_listesi.pdf`: uretim_logu'ndan üret: tür, araç/model, prompt özeti, dosya adı, filmde kullanıldığı saniye, log dosyası; müzik ve efekt kaynakları dahil.
- `out/Ad_Soyad.zip`: `storyboard/storyboard.jpg` (yoksa §4 tablosundan 6 kareli storyboard görselini PIL ile üret) + kaynak_listesi.pdf + `drive_link.txt` (içeriğini kullanıcıdan al).
- `out/youtube_aciklama.txt`: başlık "TalentCup-2026 Bir Derece", 3 cümle açıklama, kullanılan araçlar.
- `out/tanitim_notlari.md`: tanıtım videosu için malzeme listesi: hangi prompt, hangi log, hangi çıktı, filmde hangi saniye; en az 2 görsel ve 2 video prompt örneği.
- Tüm ffmpeg ve API komutları `out/komutlar.log`.

## 9. Klasörler

```
TalentCup/
  CLAUDE.md
  prompts/            # yazdığın prompt'lar (+ stil.txt)
  assets/ses/         # ses_k1.m4a, ses_k3.m4a (kullanıcı), muzik.mp3, klik.wav, tik.wav (sen)
  assets/gorseller/   # seçilen görseller
  assets/videolar/    # seçilen klipler
  storyboard/
  scripts/
  work/
  out/
```
