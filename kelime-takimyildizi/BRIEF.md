# Kelime Takımyıldızı — 30 YouTube Shorts üretimi

Ortaokul "Yaşayan Sözlük Tasarımı Yarışması" (İstanbul İl MEM, Dilimizin Zenginlikleri Projesi) için hazırlanan
"Türkçenin Kelime Hazinesi" sözlüğünün 30 kartı var. Her kartın QR kodu kendi YouTube Shorts videosuna gidecek.
Bu brif, 30 Shorts'u üretmek ve sonra QR etiketlerini çıkarmak için yazıldı. Teslim tarihi 13 Kasım 2026;
videolar en geç 4 Kasım'da hazır olmalı.

## Girdiler

- `kelimeler.csv` (UTF-8): tek veri kaynağı. Sütunlar: `id, kelime, kategori, renk, anlami, ornek_cumle, bilgi,
  higgsfield_prompt, seslendirme, youtube_baslik, youtube_aciklama`. 30 satır, id 01–30.
- Ortam değişkenleri: `ELEVENLABS_API_KEY` (zorunlu), Higgsfield için erişim bilgisi (varsa).
- Kategoriler ve renkler: Kültürümüz `#A0522D` (01–10), Eski Sözcükler `#6A3FB5` (11–20), Değerler `#C4385E` (21–30).
  Renkler basılı kartlardan alınmış yaklaşık değerlerdir.

## Klasör yapısı

```
kelime-takimyildizi/
├── BRIEF.md
├── kelimeler.csv
├── audio/      01.mp3 … 30.mp3        (G1)
├── images/     01.png … 30.png        (G2)
├── clips/      01.mp4 … 30.mp4        (G2, isteğe bağlı hareketli sahne)
├── shorts/     01_imece.mp4 …         (G3)
├── uploads/    youtube_listesi.csv    (G4)
├── links.csv                          (veli doldurur: id,url)
├── print/      qr_etiketleri.pdf      (G5)
└── scripts/
```

## G1 — Seslendirme (ElevenLabs)

1. `seslendirme` sütunundaki metni her satır için ayrı ses dosyasına çevir: `audio/NN.mp3`.
2. Türkçeyi destekleyen çok dilli bir model kullan; güncel model adını ElevenLabs dokümantasyonundan doğrula.
3. Hazır kütüphaneden sıcak, anlatıcı tonunda tek bir Türkçe ses seç; 30 dosyanın hepsinde aynı ses ve ayarlar.
   **Ses klonlama yapma.**
4. Kelime başta biraz yavaş ve net okunsun (cümleden sonra kısa bir duraklama).
5. Önce 01, 05, 06, 17 ve 26'yı üret (İmece, Yadigâr, Yâren, Sükût, Diğerkâmlık). Şapkalı harfler (â, û) doğru
   okunuyor mu, veliye dinlet ve onay al; sonra kalanları üret.

## G2 — Görseller (Higgsfield)

1. Her satırın `higgsfield_prompt` metniyle 9:16 dikey bir görsel üret: `images/NN.png`. Stil satırı her promptun
   başında hazır; 30 görsel aynı elden çıkmış gibi tutarlı olmalı.
2. İsteğe bağlı: aynı görselden 4–5 saniyelik hafif hareketli bir sahne (`clips/NN.mp4`).
3. Higgsfield'a bu ortamdan programla erişilemiyorsa dur ve veliye söyle: promptları `scripts/higgsfield_promptlari.txt`
   olarak çıkar; veli görselleri Higgsfield arayüzünde üretip `images/NN.png` adıyla koyar.
4. Kural: gerçek kişi yüzü, yazı, harf, logo yok. Görselde metin çıkarsa o görseli yeniden üret.
5. Önce 3 örnek üret (01, 11, 21 — her kategoriden bir), veliye göster, stil onayı al; sonra kalanları.

## G3 — Shorts montajı (ffmpeg)

Her satır için `shorts/NN_slug.mp4` (slug: kelimenin ASCII hali, ör. `01_imece`, `26_digerkamlik`).

- 1080×1920, 30 fps, H.264 + AAC. Süre = ses süresi + 3 sn, en çok 40 sn.
- Üst bant (yaklaşık 180 px): kategori renginde; solda kategori adı büyük harfle (Türkçe büyük harf kuralıyla:
  i → İ, ı → I), sağda `NN/30`.
- İlk 2,5 sn: ekranın ortasında kelime çok büyük; görsel arkasında hafif koyulaştırılmış.
- Sonra: görsel ekranı doldurur (`clips/NN.mp4` varsa o, yoksa yavaş yakınlaşma 1,00 → 1,08).
- Altyazı: `seslendirme` metni, en çok 6–7 kelimelik parçalar, ses süresine orantılı dağıtılmış; alt üçte birde,
  yarı saydam koyu şerit üzerinde beyaz yazı. Mümkünse kelime zamanlaması için ElevenLabs'in zaman damgası
  çıktısını kullan.
- Son 2 sn: koyu zemin üzerinde "Kelime Takımyıldızı · Türkçenin Kelime Hazinesi", altında küçük harflerle
  "Seslendirme ve görseller yapay zekâ ile üretilmiştir."
- Müzik yok.
- Font: Türkçe karakterleri (ç ğ ı İ ö ş ü â î û) eksiksiz gösteren bir font (ör. Noto Sans). Her videoda bu
  karakterlerin doğru çıktığını kontrol et.

## G4 — YouTube yükleme listesi

`uploads/youtube_listesi.csv`: dosya adı, `youtube_baslik`, `youtube_aciklama`, oynatma listesi (kategori adı).
Yüklemeyi veli elle yapar:
- Görünürlük: **Liste dışı**. Kitle: **Çocuklar için yapıldı**.
- Üç oynatma listesi: Kültürümüz, Eski Sözcükler, Değerler.
- Her videonun linki `links.csv` dosyasına yazılır: `id,url` (ör. `01,https://youtube.com/shorts/XXXX`).

## G5 — QR etiketleri

`links.csv` geldikten sonra:
1. URL biçimini doğrula (youtube.com/shorts/…, youtu.be/… ya da youtube.com/watch?v=…). Eksik ya da hatalı satırı raporla.
2. Statik QR, hata düzeltme seviyesi Q, 4 modül sessiz alan, 25×25 mm, 300 dpi.
3. Her QR'ın altına küçük etiket: `NN · Kelime`.
4. `print/qr_etiketleri.pdf`: A4, kesim işaretli ızgara; sayfa kenarında "%100 ölçekte basın, sayfaya sığdırmayın".
5. Doğrulama: üretilen her QR'ı opencv/pyzbar ile geri oku, URL'yle birebir eşleştiğini raporla.

## Kabul kriterleri

1. 30 ses, 30 görsel, 30 Shorts; her biri doğru id ile eşleşiyor.
2. Hiçbir görselde yazı, logo ya da gerçek kişi yüzü yok; stil tutarlı.
3. Her Shorts 1080×1920, en çok 40 sn, altyazıda Türkçe karakterler doğru.
4. 30 QR'ın 30'u da geri okumada doğru linki veriyor.
5. Onay noktaları (G1 adım 5, G2 adım 5) atlanmadı.
