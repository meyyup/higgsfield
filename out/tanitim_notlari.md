# Tanıtım videosu notları · Son Damla

Tanıtım videosunda "nasıl yapıldı" akışını göstermek için malzeme listesi. Tüm yollar repo köküne göre.

## Akış

1. Fikir ve senaryo: `out/senaryo_son_damla.md` (6 sahne, 60 sn).
2. Referanslar (Grok Imagine Image 2.0): Damla karakter kartı ve orman mekânı, 2'şer aday, kullanıcı seçti (`out/adaylar/`).
3. Sahne kareleri: referanslardan düzenleme (Qwen Image 3 Edit; K6 filiz karesi text-to-image), her kare 2 aday (seed 1101/2202).
4. Klipler: her kare Seedance 2.0 ile 4–6 sn hareketli klibe çevrildi (720p, ses kapalı).
5. Ses: ElevenLabs Voice Design ile 3'er aday, Damla 2 ve Pıt 1 seçildi; 5 replik okundu.
6. Montaj: `scripts/sd_montaj.py` (ffmpeg + PIL), yazılar, altyazı, müzik ve efekt miksajı.
7. Kontrol: `out/kontrol.md`, kaynaklar: `out/kaynak_listesi.pdf`.

## Malzeme listesi

| Tür | Prompt | Log | Çıktı | Filmde (sn) |
| --- | --- | --- | --- | --- |
| Görsel | `prompts/sd_damla_ref.txt` | `out/uretim_logu/sd_damla_ref_B.json` | `assets/gorseller/sd_damla_ref.png (aday B)` | doğrudan yok (karakter/mekân referansı) |
| Görsel | `prompts/sd_orman_ref.txt` | `out/uretim_logu/sd_orman_ref_B.json` | `assets/gorseller/sd_orman_ref.png (aday B)` | doğrudan yok (karakter/mekân referansı) |
| Görsel | `prompts/sd_k1_bulut.txt` | `out/uretim_logu/sd_k1_bulut_B.json` | `assets/gorseller/sd_k1_bulut.png (aday B)` | 0–6 (klibin ilk karesi) |
| Görsel | `prompts/sd_k2_alev.txt` | `out/uretim_logu/sd_k2_alev_A.json` | `assets/gorseller/sd_k2_alev.png (aday A)` | 11,5–17 (klibin ilk karesi) |
| Görsel | `prompts/sd_k2_mercek.txt` | `out/uretim_logu/sd_k2_mercek_A.json` | `assets/gorseller/sd_k2_mercek.png (aday A)` | 6–11,5 (klibin ilk karesi) |
| Görsel | `prompts/sd_k2_yorgun.txt` | `out/uretim_logu/sd_k2_yorgun_A.json` | `assets/gorseller/sd_k2_yorgun.png (aday A)` | 17–20 (klibin ilk karesi) |
| Görsel | `prompts/sd_k3_bulus.txt` | `out/uretim_logu/sd_k3_bulus_A.json` | `assets/gorseller/sd_k3_bulus.png (aday A)` | 24–28 (klibin ilk karesi) |
| Görsel | `prompts/sd_k3_saganak.txt` | `out/uretim_logu/sd_k3_saganak_A.json` | `assets/gorseller/sd_k3_saganak.png (aday A)` | 20–24 (klibin ilk karesi) |
| Görsel | `prompts/sd_k4_kutu.txt` | `out/uretim_logu/sd_k4_kutu_B.json` | `assets/gorseller/sd_k4_kutu.png (aday B)` | 34–40 (klibin ilk karesi) |
| Görsel | `prompts/sd_k4_toplama.txt` | `out/uretim_logu/sd_k4_toplama_B.json` | `assets/gorseller/sd_k4_toplama.png (aday B)` | 28–34 (klibin ilk karesi) |
| Görsel | `prompts/sd_k5_temiz.txt` | `out/uretim_logu/sd_k5_temiz_B.json` | `assets/gorseller/sd_k5_temiz.png (aday B)` | 40–50 (klibin ilk karesi) |
| Görsel | `prompts/sd_k6_filiz.txt` | `out/uretim_logu/sd_k6_filiz_A.json` | `assets/gorseller/sd_k6_filiz.png (aday A)` | 50–60 (klibin ilk karesi) |
| Görsel | `prompts/sd_k6_yaprak.txt` | `out/uretim_logu/sd_k6_yaprak_A.json` | `assets/gorseller/sd_k6_yaprak.png (aday A)` | 50–60 (klibin ilk karesi) |
| Video | `prompts/sd_c01_bulut.txt` | `out/uretim_logu/sd_c01_bulut.json` | `out/adaylar/sd_c01_bulut.mp4` | 0–6 |
| Video | `prompts/sd_c02_mercek.txt` | `out/uretim_logu/sd_c02_mercek.json` | `out/adaylar/sd_c02_mercek.mp4` | 6–11,5 |
| Video | `prompts/sd_c03_alev.txt` | `out/uretim_logu/sd_c03_alev.json` | `out/adaylar/sd_c03_alev.mp4` | 11,5–17 |
| Video | `prompts/sd_c04_yorgun.txt` | `out/uretim_logu/sd_c04_yorgun.json` | `out/adaylar/sd_c04_yorgun.mp4` | 17–20 |
| Video | `prompts/sd_c05_saganak.txt` | `out/uretim_logu/sd_c05_saganak.json` | `out/adaylar/sd_c05_saganak.mp4` | 20–24 |
| Video | `prompts/sd_c06_bulus.txt` | `out/uretim_logu/sd_c06_bulus.json` | `out/adaylar/sd_c06_bulus.mp4` | 24–28 |
| Video | `prompts/sd_c07_toplama.txt` | `out/uretim_logu/sd_c07_toplama.json` | `out/adaylar/sd_c07_toplama.mp4` | 28–34 |
| Video | `prompts/sd_c08_kutu.txt` | `out/uretim_logu/sd_c08_kutu.json` | `out/adaylar/sd_c08_kutu.mp4` | 34–40 |
| Video | `prompts/sd_c09_temiz.txt` | `out/uretim_logu/sd_c09_temiz.json` | `out/adaylar/sd_c09_temiz.mp4` | 40–50 |
| Video | `prompts/sd_c10_yaprak.txt` | `out/uretim_logu/sd_c10_yaprak.json` | `out/adaylar/sd_c10_yaprak.mp4` | 50–60 |
| Konuşma | script içinde (`scripts/sd_elevenlabs.py`) | `out/uretim_logu/elevenlabs_sd_s1_damla.json` | `assets/ses/elevenlabs/sd_s1_damla.mp3` | 0,3–5,5 |
| Konuşma | script içinde (`scripts/sd_elevenlabs.py`) | `out/uretim_logu/elevenlabs_sd_s2_pit.json` | `assets/ses/elevenlabs/sd_s2_pit.mp3` | 17,2–19,2 |
| Konuşma | script içinde (`scripts/sd_elevenlabs.py`) | `out/uretim_logu/elevenlabs_sd_s3_damla.json` | `assets/ses/elevenlabs/sd_s3_damla.mp3` | 22–27,1 |
| Konuşma | script içinde (`scripts/sd_elevenlabs.py`) | `out/uretim_logu/elevenlabs_sd_s4_damla.json` | `assets/ses/elevenlabs/sd_s4_damla.mp3` | 29–34,7 |
| Konuşma | script içinde (`scripts/sd_elevenlabs.py`) | `out/uretim_logu/elevenlabs_sd_s5_pit.json` | `assets/ses/elevenlabs/sd_s5_pit.mp3` | 44,5–46,1 |

## Görsel prompt örnekleri

### sd_damla_ref (aday B) · xai/grok-imagine-image-2.0

Referans: yok · Log: `out/uretim_logu/sd_damla_ref_B.json` · Çıktı: `assets/gorseller/sd_damla_ref.png`

```
Character design sheet of "Damla", a cute raindrop character: a classic teardrop-shaped water droplet, transparent light-blue water with soft refractions and a bright white highlight near the top, big curious friendly eyes, small expressive eyebrows, a small smiling mouth, two tiny thin arms, no legs, no clothes, no accessories. Three views side by side on a plain light grey background: front view smiling, three-quarter view looking determined, front view worried. Same character in all three views, consistent shape, size and color. No text, no logos. 16:9.

3D animated feature film still, Pixar-like stylized characters in a realistic cinematic environment, warm golden light, soft shadows, rich colors
```

### sd_k2_mercek (aday A) · alibaba/qwen-image-3/edit

Referans: assets/gorseller/sd_orman_ref.png · Log: `out/uretim_logu/sd_k2_mercek_A.json` · Çıktı: `assets/gorseller/sd_k2_mercek.png`

```
Low close-up on the ground of the pine forest clearing from the location reference: dry yellow grass, pine trees, the green recycling bin for glass on the right. A discarded green glass bottle lies on dry grass; the bright sunlight passes through the glass and is focused into one tiny, intensely bright white spot on the dry grass, with a thin curl of smoke rising from that spot. Shallow depth of field. No people, no logos, no readable text. 16:9.

3D animated feature film still, Pixar-like stylized characters in a realistic cinematic environment, warm golden light, soft shadows, rich colors
```

### sd_k4_toplama (aday B) · alibaba/qwen-image-3/edit

Referans: assets/gorseller/sd_damla_ref.png, assets/gorseller/sd_orman_ref.png · Log: `out/uretim_logu/sd_k4_toplama_B.json` · Çıktı: `assets/gorseller/sd_k4_toplama.png`

```
Wide shot of the pine forest clearing from the location reference: dry yellow grass, pine trees, the green recycling bin for glass on the right, morning after the fire, a few green sprouts in the burnt grass. Damla, the raindrop character from the reference sheet: a round classic teardrop-shaped water droplet, transparent light-blue water with a white highlight, big warm brown eyes, small eyebrows, two thin transparent arms. Keep her design exactly as in the reference leads her two friends of the same raindrop design: Pıt, a smaller droplet, and Şıp, a bigger droplet (no clothes, no accessories) and many other raindrops; together they form a small sparkling stream that rolls the discarded glass bottles across the ground toward the green recycling bin. Cheerful, busy, playful. No people, no logos, no readable text. 16:9.

3D animated feature film still, Pixar-like stylized characters in a realistic cinematic environment, warm golden light, soft shadows, rich colors
```

## Video prompt örnekleri

### sd_c02_mercek · bytedance/seedance-2.0/image-to-video · filmde 6–11,5 sn

Başlangıç karesi: assets/gorseller/sd_k2_mercek.png · Parametreler: {"duration": 5, "resolution": "720p", "generate_audio": false} · Log: `out/uretim_logu/sd_c02_mercek.json`

```
The focused sunlight spot on the dry grass grows brighter, smoke thickens, and a small flame ignites and starts to spread. Static camera. Keep the character design consistent. Smooth natural motion.

3D animated feature film still, Pixar-like stylized characters in a realistic cinematic environment, warm golden light, soft shadows, rich colors
```

### sd_c07_toplama · bytedance/seedance-2.0/image-to-video · filmde 28–34 sn

Başlangıç karesi: assets/gorseller/sd_k4_toplama.png · Parametreler: {"duration": 5, "resolution": "720p", "generate_audio": false} · Log: `out/uretim_logu/sd_c07_toplama.json`

```
The raindrops' little stream rolls the glass bottles across the ground toward the green recycling bin; Damla turns to the camera and speaks happily. Slow sideways tracking shot. Keep the character design consistent. Smooth natural motion.

3D animated feature film still, Pixar-like stylized characters in a realistic cinematic environment, warm golden light, soft shadows, rich colors
```

### sd_c10_yaprak · bytedance/seedance-2.0/image-to-video · filmde 50–60 sn

Başlangıç karesi: assets/gorseller/sd_k6_yaprak.png, assets/gorseller/sd_k6_filiz.png · Parametreler: {"duration": 5, "resolution": "720p", "generate_audio": false} · Log: `out/uretim_logu/sd_c10_yaprak.json`

```
Damla winks at the camera, lets go of the leaf tip and falls down onto the soil with a tiny splash; a small green sprout grows up from that spot. Camera tilts down with her. Keep the character design consistent. Smooth natural motion.

3D animated feature film still, Pixar-like stylized characters in a realistic cinematic environment, warm golden light, soft shadows, rich colors
```

## Ses tasarımı örneği

ElevenLabs Voice Design, Damla (`out/uretim_logu/elevenlabs_tasarla_damla.json`):

```
Female voice actor performing a cheerful, brave animated cartoon heroine, a tiny raindrop, in Turkish. Bright, light, high-pitched, warm and expressive, slightly breathless. Clear studio recording.
```

Not: Tarifte çocuk yaşı geçince ElevenLabs isteği güvenlik filtresiyle engelledi; tarif "çizgi film karakteri" olarak yeniden yazıldı. Tanıtımda anlatılabilecek bir üretim anı.

## Gösterilebilecek ara çıktılar

- Aday karşılaştırmaları: `out/adaylar/` (A/B), reddedilenler `out/adaylar/reddedilen/`
- Ses adayları sayfası: `out/sd_ses_adaylari.html`
- Storyboard: `storyboard/storyboard.jpg`
- c04_yorgun klibinin yalnızca ilk 2,5 sn'si kullanıldı (sonra damlalar birbirine kaynıyor): kabul/ret örneği.
