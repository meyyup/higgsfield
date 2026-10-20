# Devir notu: Son Damla (TalentCup-2026)

Dal: `claude/peaceful-ride-qr1zgz`. Her şey bu dala push edildi. Yeni oturumda önce bunu oku.

## Durum (2026-10-20)

Aktif film: **SON DAMLA**. 60 sn, 3D animasyon. Başrolde bir yağmur damlası: Damla ve arkadaşları yangını söndürmekte zorlanıyor. Sebep ormana atılan cam şişeler, çünkü güneşi mercek gibi topluyorlar. Damlalar şişeleri geri dönüşüme taşıyor ve bir sonraki yaz yangın çıkmıyor.
- Senaryo: `out/senaryo_son_damla.md`. Repliklerin kesin metni `scripts/sd_montaj.py` → `KONUSMA` listesinde.
- Final video: `out/TalentCup-2026_Son_Damla.mp4` (1080p, 25 fps, −13,7 LUFS). Küçük kopya: `out/TalentCup-2026_Son_Damla_720p.mp4`. Altyazı: `out/sd_altyazi.srt`.
- **Seslendirme tamam (ElevenLabs).** Voice Design adaylarından kullanıcı Damla 2 ve Pıt 1'i seçti (`assets/ses/elevenlabs/sesler.json`). Replikler `eleven_multilingual_v2` ile okundu: 5,2 / 2,0 / 5,1 / 5,7 / 1,6 sn. Montaj yenilendi (60,0 sn, −13,5 LUFS), 720p kopya da güncel. Notlar: Voice Design örnek metni en az 100 karakter olmalı; tarifte çocuk yaşı geçince istek güvenlik filtresine takılıyor, bu yüzden tarif "çizgi film karakteri" diye yazıldı.
- **Sıradaki iş:** teslim paketi hazır; yalnızca zip kaldı (Ad_Soyad + Drive linki bekleniyor, 6. adım).

`CLAUDE.md` eski ±1°C filminin brifi. Klasör yapısı, loglama ve DUR kuralları Son Damla için de geçerli; içerik ve stil kısmı geçerli değil. ±1°C v2'nin (`prompts/v2_*`) ana kadraj seçimi askıda. Kullanıcı yeni fikre geçti, bu yüzden dokunma.

## Sıradaki adımlar
1. Anahtarın gelip gelmediğini kontrol et: `python3 scripts/sd_elevenlabs.py tasarla`. Script Damla ve Pıt için Voice Design adaylarını `assets/ses/elevenlabs/aday_*.mp3` olarak yazar.
   - **Uç noktalar test edilmedi.** Önceki oturumda anahtar yoktu, script ilk kez burada çalışacak. Hata alırsan ElevenLabs dokümanına bakıp düzelt: `/v1/text-to-voice/design`, `/v1/text-to-voice`, `/v1/text-to-speech/{id}`.
2. Adayları kullanıcıya `SendUserFile` ile gönder ve seçtir (**DUR**).
3. `python3 scripts/sd_elevenlabs.py sec damla=<n> pit=<n>`, ardından `python3 scripts/sd_elevenlabs.py oku`.
4. `python3 scripts/sd_montaj.py --yalniz-ses`. Görüntü `work/sd/` içinden yeniden kullanılır. `work/` gitignore'da; yeni oturumda yoksa script `--yalniz-ses` bayrağını yok sayar ve tam montaj yapar (~4 dk). Montaj ElevenLabs dosyalarını otomatik seçer ve onlarda perde kaydırmayı kapatır.
   - Replik süreleri değişirse `KONUSMA` listesindeki başlangıç saniyelerine bak. Mevcut sentez sesle süreler: 5,7 / 2,6 / 5,9 / 6,6 / 2,6 sn. Sahne sınırları: 0–6, 6–20, 20–28, 28–40, 40–50, 50–60.
5. 720p kopyayı yeniden üret: `ffmpeg -i out/TalentCup-2026_Son_Damla.mp4 -c:v libx264 -crf 26 -preset slow -vf scale=1280:720 -c:a aac -b:a 160k -movflags +faststart out/TalentCup-2026_Son_Damla_720p.mp4`. Ardından commit, push ve `SendUserFile`.
6. Teslim paketi: `python3 scripts/sd_teslim.py` → kontrol.md (17/17 geçti), kaynak_listesi.pdf, storyboard/storyboard.jpg, youtube_aciklama.txt, tanitim_notlari.md. **Zip bekliyor:** kullanıcıdan Ad_Soyad ve Drive linki gelince `out/drive_link.txt` yaz, `python3 scripts/sd_teslim.py --ad Ad_Soyad`.
7. Drive: kullanıcı videoyu kendisi yükleyecek. Drive aracı içeriği base64 olarak istiyor, video için pratik değil. Linki gelince `drive_link.txt` dosyasına yaz.

## Üretim hattı (Son Damla)
| Adım | Script | Not |
| --- | --- | --- |
| Prompt'lar | `scripts/prompts_sd.py` → `prompts/sd_*.txt` | Stil: `prompts/sd_stil.txt` |
| Anahtar kareler | `scripts/sd_kareler.py [ad...]` | `alibaba/qwen-image-3/edit`, 2 aday (seed 1101/2202); referanslar `assets/gorseller/sd_damla_ref.png`, `sd_orman_ref.png` |
| Klipler | `scripts/sd_klipler.py [ad...]` | `bytedance/seedance-2.0/image-to-video`, 720p, ses kapalı |
| Efekt | `scripts/sd_ses.py` → `assets/ses/sd_efekt.wav` | numpy sentezi, özgün |
| Müzik | `scripts/sd_muzik_indir.sh` → `assets/ses/kutuphane/` | Kevin MacLeod: Heartwarming, Volatile Reaction, Lasting Hope, Carefree |
| Konuşma | `scripts/sd_elevenlabs.py` (yeni) / `scripts/sd_tts.sh` (geçici) | Öncelik: `assets/ses/*.m4a` → `assets/ses/elevenlabs/` → `work/tts/` |
| Montaj | `scripts/sd_montaj.py [--yalniz-ses]` | Çapraz geçiş 0,35 sn; PIL yazı katmanı; müzik konuşma altında tam −12 dB |

Seçilen kareler `assets/gorseller/sd_k*.png`'de. Reddedilenler `out/adaylar/reddedilen/` altında. c04_yorgun klibinden yalnızca ilk 2,5 sn kullanılıyor, çünkü sonrasında damlalar birbirine kaynıyor.

## Bilinen tuzaklar
- **Higgsfield:** REST API `https://api.higgsfield.ai`, `Authorization: Key $HIGGSFIELD_API_KEY` (key_id:secret). API kredisi Console bakiyesinden düşer; uygulamanın Plus kredisi ayrı bir bakiye. Fiyat için `/estimate/<model>` kullan.
  - Seedance 1.5 Pro ve Nano Banana REST API'de yok.
  - Seedance image-to-video `aspect_ratio` kabul etmiyor (şemada additionalProperties: false).
  - CLI (`higgsfield`) OAuth istiyor, bu ortamda çalışmıyor.
- **ffmpeg:** `tpad` ile başa sabit kare eklenince zaman damgaları bozuluyor ve kodlayıcı kare atıyor. `setpts=N/25/TB` bu yüzden var, kaldırma.
- **edge-tts:** Proxy sertifikası nedeniyle `scripts/edge_tts_proxy.py` üzerinden çalışıyor (`/root/.ccr/ca-bundle.crt`).
- **Dosya boyutu:** Videolar repoda; GitHub büyük dosya uyarısı veriyor ama push çalışıyor.
- **Kredi:** Son Damla için ~270 Higgsfield API kredisi harcandı (görsel ~30, klip ~240).

## Kullanıcı tercihleri
- Türkçe yazışıyor; kısa ve net özet istiyor.
- Kendi seçimi gereken noktalarda adayları görsel karşılaştırma sayfasıyla gösterip durmak gerekiyor.
- Bilimsel doğruluk önemli. "Çoğu zaman cam şişe" ifadesi bu yüzden "yangın başlatabiliyor" olarak yumuşatıldı; kullanıcı kabul etti.
