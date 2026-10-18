# Eksiklerin Tamamlanma Planı

Her madde: **ne yapılacak, nasıl yapılacak, hangi güne ekleniyor.**

---

## 1. Pano teknik çizimi — ✅ ARTIK İNCELENDİ

Gerçek boyutlar bulundu: **1600mm (genişlik) × 1500mm (yükseklik) × 450mm
(derinlik)**. Ön yüzde sigorta sıraları, bir "Modem" kutusu (yani panoda
zaten bir haberleşme cihazı öngörülmüş!) ve "En az 400mm" diye işaretli
bir kablo boşluğu var.

**Ne yapmanız gerekiyor (Gün 7'ye ekleniyor):**
- Blok şemanızı bu gerçek 1600×1500×450mm ölçülerine göre çizin
- Sensör modülünüzü, çizimdeki **"Modem" kutusunun yanına** yerleştirilecek
  şekilde konumlandırın — "mevcut haberleşme altyapısına yakın konumlandırma"
  diyebilirsiniz, bu gerçekçilik katar
- Kablosuz sensörleri, sigorta sıralarının **üstündeki boş alana** (çizimde
  görünen üst boşluk) yerleştirmeyi önerin — kablo kalabalığına dokunmadan

---

## 2. AG PANO MALZEME ŞARTNAMESİ — ✅ ARTIK İNCELENDİ

Gerçek çevresel tasarım koşulları bulundu:

| Koşul | Değer (dahili/bina içi) |
|---|---|
| Ortam sıcaklığı - en çok | 40°C |
| Ortam sıcaklığı - en az | -5°C |
| Bağıl nem | +20°C'de **%90**, +40°C'de %50 |
| Kirlilik derecesi | Düzey II |
| Koruma derecesi | IP2X (en az) |
| EMI notu | "Cihazlar elektromanyetik alanlardan zarar görmeyecek biçimde yerleştirilecek" |

**Ne yapmanız gerekiyor:**
- **`config.py`'daki nem eşiğini güncelleyin** — şu an ≤60 normal diyoruz
  ama şartname %90 bağıl nemi normal ortam koşulu sayıyor. Yeni öneri:
  Normal ≤70%, Uyarı 70-90%, Kritik >90% (aşağıda güncelledim)
- Fiziksel modül dokümanınıza (Gün 7) şu cümleyi ekleyin: *"Sensör modülü
  IP2X koruma dereceli bir muhafaza içinde, -5°C/+40°C ortam sıcaklığı ve
  %90 bağıl neme dayanıklı seçilmiştir; elektromanyetik alan etkisini
  azaltmak için ana barlardan ve TMK'lardan uzak, sinyal kablolarında
  bükümlü/ekranlı kablo kullanılmıştır"* — bu, jüriye şartnameyi gerçekten
  okuduğunuzu gösterir

---

## 3. Sistem mimarisi diyagramı — eksik bir görev olarak eklendi

Şu ana kadar plan sadece Gün 7'de donanım blok şemasını içeriyordu; **uçtan
uca yazılım+donanım mimarisi diyagramı** ayrı bir iş olarak hiç yoktu.
Şimdi hazırladım (aşağıya bakın) — Gün 8'deki sunuma doğrudan koyabilirsiniz.

---

## 4. Nem sensörü — gerçek ürün seçildi: **SHT31**

Akım/PD/ark flaşı gerçek ürünlere dayanıyordu, nem eksikti. **SHT31**
(Sensirion) yaygın, ucuz, endüstriyel projelerde sık kullanılan bir
sıcaklık+nem sensörüdür:
- Ölçüm aralığı: 0-100% RH, -40°C ile +90°C
- Doğruluk: ±2% RH
- I2C haberleşme (mikrodenetleyiciye kolay bağlanır)

**Ne yapmanız gerekiyor:** Gün 7'deki bileşen listesine "SHT31 (sıcaklık+nem,
I2C)" olarak ekleyin — hem sıcaklık hem nemi tek sensörle çözmüş olursunuz,
bu maliyet/sadelik açısından da olumlu bir tasarım kararı olarak sunulabilir.

---

## 5. Ölçeklenebilirlik — "iddia" değil "kanıt" haline getirme

Şu an plan sadece Gün 7'de yazılı bir paragraf öngörüyordu. Bunun yerine
**gerçekten çalıştırıp gösterme** öneriyorum.

**Ne yapmanız gerekiyor (Gün 5-6 arasına eklenir):**
- `config.py`'daki `PANEL_IDS` listesini geçici olarak 3'ten **50-100
  panele** çıkarın (`P-01` ... `P-100` gibi otomatik üretin)
- `sensor_simulator.py`'ı bu şekilde birkaç dakika çalıştırıp InfluxDB'nin
  ve Grafana'nın bunu sorunsuz işlediğini gösterin
- Sunumda "100 modül ile test ettik, sistem sorunsuz çalıştı" diyebilir,
  ekran görüntüsü/kısa video ekleyebilirsiniz — bu, sadece iddia etmekten
  çok daha güçlü bir kanıttır

---

## 6. Risk skoruna nem ve PD'nin dahil edilmesi

Gün 4'teki "birlikte değerlendirme" mantığı şu an sadece sıcaklık+akımı
kapsıyor. Gün 4'te `detector.py` yazarken şu genişletilmiş mantığı kullanın:

```
risk_skoru = 0
sicaklik KRİTİK ise +40, UYARI ise +15
akim KRİTİK ise +40, UYARI ise +15
pd_level KRİTİK ise +15, UYARI ise +5
nem KRİTİK ise +10, UYARI ise +5
arc_trip True ise -> risk_skoru = 100 (anında, diğer hesaba bakmadan)

# Birlikte tetiklenme çarpanı:
eğer (sicaklik UYARI/KRİTİK) VE (akim UYARI/KRİTİK) ise:
    risk_skoru = risk_skoru * 1.3   # ikisi birlikte yükseliyorsa daha tehlikeli
```

Bu mantığı Gün 4'te `detector.py` yazarken birebir kullanabilirsiniz.

---

## 7. PD'nin Modbus haritasındaki yeri — karar verildi

PD sensörü (HFCT) gerçekte analog çıkışlı, doğrudan Modbus register'ı yok.
**Karar:** Modbus haritalama tablonuza PD'yi şöyle ekleyin:

| Veri | Adres | Not |
|---|---|---|
| PD seviyesi (pC) | 40020 (özel/uydurma adres) | *"HFCT sensörden gelen analog sinyal, ayrı bir PD analiz kartında dijitalleştirilip bu adrese yazılır"* |

Bu şekilde hem gerçekçi kalırsınız (gerçek cihazın Modbus'ı yoktur demek
yerine, "ek bir dönüştürücü katman var" diye açıklarsınız) hem de haritada
4 verinin de yeri olur. Gün 6'ya ekleyin.

---

## 8. Operatör alarm onayı — basit bir adım eklendi

Şu an plan "SMS gönderildi" ile bitiyor, operasyon ekibinin alarmı nasıl
**kapattığı/onayladığı** gösterilmiyor.

**Ne yapmanız gerekiyor (Gün 6'ya eklenir, basit versiyon):**
- InfluxDB'ye/CSV'ye yazdığınız alarm kaydına bir `onaylandi: false` alanı
  ekleyin
- Grafana dashboard'da bu alanı gösteren bir tablo yapın
- Gerçek bir "onayla" butonu kurmak zaman alır; bunun yerine sunumda
  "gerçek sistemde operatör bu alarmı SCADA ekranından onaylar, biz bunu
  basitleştirilmiş bir tabloyla gösteriyoruz" demeniz yeterli — jüri
  operasyon akışının **düşünülmüş olduğunu** görmek istiyor, illa tam
  çalışan bir buton istemiyor

---

## Özet: Hangi güne ne eklendi

| Gün | Eklenen iş |
|---|---|
| Gün 4 | Risk skoruna nem+PD dahil etme, "birlikte tetiklenme" çarpanı |
| Gün 5-6 arası | 50-100 panelle ölçeklenebilirlik testi |
| Gün 6 | PD'nin Modbus haritasındaki yeri, operatör alarm onayı tablosu |
| Gün 7 | Gerçek pano ölçülerine göre blok şema, SHT31 nem sensörü, IP2X/EMI notları |
| Gün 8 | Uçtan uca mimari diyagramı (aşağıda hazır) |

## config.py'da güncellenmesi gereken tek şey: nem eşiği

Şartnameye göre %90 nem normal kabul edildiğinden, mevcut eşik çok düşük.
İsterseniz hemen güncelleyip size yeni dosyayı vereyim mi?
