# Tanıtım videosu · okunacak metin ve kayıt rehberi

Mert, bu metni kendi sesinle okuyacaksın. Yüzün görünmeyecek, yalnızca sesin. Görüntüler hazır: kayıtlar gelince video sesinin uzunluğuna göre kendiliğinden ayarlanacak.

## Nasıl kaydedilir?

1. Telefonun ses kaydedicisini aç (iPhone: Sesli Notlar, Android: Ses Kaydedici).
2. Sessiz bir oda seç; halı, perde ve koltuk olan bir oda yankıyı azaltır. Telefonu ağzından bir karış uzakta tut.
3. **Her bölümü ayrı bir dosya olarak kaydet** ve dosyanın adını bölüm numarası yap: `t01`, `t02`, `t04` … `t13`. `t03` yok, orada filmin kendi sesi çalıyor.
4. Kayda başlayınca 1 saniye bekle, sonra oku. Bitince 1 saniye daha bekle ve durdur.
5. Acele etme, gülümseyerek ve normal konuşur gibi oku. Takılırsan o bölümü baştan kaydetmen yeterli.
6. Metni birebir okumak zorunda değilsin; kendi cümlelerinle de söyleyebilirsin. Video senin kaydının uzunluğuna uyar.

Dosyaları bana iletmek için: Google Drive'a bir klasör aç, kayıtları oraya yükle ve linkini gönder. Ya da GitHub'da `assets/ses/tanitim/` klasörüne yükle.

Tahmini toplam süre: **156 sn** (şart: 60–180 sn).

## Metin

### t01 · Açılış  (0–10. sn)

> Merhaba, ben Mert. TalentCup için Son Damla adında bir dakikalık bir animasyon film yaptım. Bu videoda filmimi nasıl yaptığımı anlatacağım.

### t02 · Filmin konusu  (10–29. sn)

> Filmin kahramanı Damla adında bir yağmur damlası. Damla ve arkadaşları orman yangınlarını söndürmekte çok zorlanıyor. Sonra yangını başlatan şeyin ormana atılan cam şişeler olduğunu fark ediyorlar, çünkü cam şişe güneşi büyüteç gibi topluyor. Şimdi filmden kısa bir bölüm izleyelim.

### t03 · Filmden bir bölüm (anlatım yok, filmin kendi sesi)  (29–43. sn)

_Kayıt yok: burada filmden 14 saniyelik bir bölüm sesiyle oynuyor._

### t04 · Storyboard  (43–55. sn)

> Önce filmi altı sahneye böldüm ve bir storyboard hazırladım. Her sahne için bir anahtar kare var: bulut, yangın, fark ediş, temizlik, yeni yaz ve kapanış.

### t05 · Bir kare nasıl sahneye dönüştü?  (55–71. sn)

> Mesela ikinci sahnedeki bu kareye bakalım. Önce yapay zekâya, şişeden geçen güneşin kuru otu yaktığı bir görsel çizdirdim. Sonra bu görseli video modeline verip alevin büyümesini istedim. Bu klip filmin altıncı saniyesinde başlıyor.

### t06 · Araçlar  (71–85. sn)

> Bu filmi Claude, Higgsfield ve ElevenLabs kullanarak, babamın yardımıyla yaptım. Görselleri ve videoları Higgsfield ile, karakterlerin seslerini ElevenLabs ile yaptım. Claude da prompt yazmama ve montaja yardım etti.

### t07 · Görsel prompt 1  (85–97. sn)

> İlk görsel promptum Damla'nın karakter kartı. İki aday ürettim ve en beğendiğimi seçtim. Damla her sahnede aynı görünsün diye bu kartı referans olarak kullandım.

### t08 · Görsel prompt 2  (97–107. sn)

> İkinci görsel promptum dördüncü sahne: damlalar küçük bir dere olup şişeleri geri dönüşüm kutusuna taşıyor. Burada da iki adaydan birini seçtim.

### t09 · Video prompt 1  (107–118. sn)

> İlk video promptumda, damlaların deresi şişeleri kutuya doğru yuvarlıyor. Damla da kameraya dönüp konuşuyor. Başlangıç karesi olarak bir önceki görseli verdim.

### t10 · Video prompt 2  (118–127. sn)

> İkinci video promptumda Damla göz kırpıyor, yapraktan düşüyor ve düştüğü yerde bir filiz çıkıyor. Bu, filmin son sahnesi.

### t11 · Üretim kayıtları  (127–137. sn)

> Her üretimin kaydını tuttum. Kayıtlarda zaman, model, promptun tamamı ve çıkan dosyanın adı yazıyor. Sonra hepsini bir kaynak listesinde topladım.

### t12 · Filmde nerede kullanıldı?  (137–150. sn)

> Son olarak bu görsel ve videoların filmde nerede olduğuna bakalım. Mercek sahnesi altıncı saniyede, toplama sahnesi yirmi sekizinci saniyede, son sahne de ellinci saniyede başlıyor.

### t13 · Kapanış  (150–156. sn)

> Filmimin mesajı şu: Ateşi söndürmek zor, başlamasını önlemek kolay. İzlediğiniz için teşekkürler!

## Şartlarla eşleşme

| Şart | Bölüm |
| --- | --- |
| Filmin konusu ve filmden bir bölüm | t02, t03 |
| Storyboard ve bir karenin sahneye dönüşmesi | t04, t05 |
| Kullanılan araçlar | t06 (ekranda model adları da yazıyor) |
| En az 2 görsel prompt | t07 (Damla karakter kartı), t08 (toplama sahnesi) |
| En az 2 video prompt | t09 (toplama klibi), t10 (yaprak klibi) |
| Üretim kayıtları ve sonuçları | t07–t10 (sonuçlar), t11 (kayıtlar, kaynak listesi) |
| Görsellerin ve videoların filmdeki yerleri | t05, t12 |

## Son adım

Final video `out/tanitim/TalentCup-2026_Son_Damla_Tanitim.mp4` olarak çıkacak. Onu Google Drive'a yükle, paylaşımı **Bağlantıya sahip olan herkes · Görüntüleyen** yap ve linki yarışmaya gönder.
