# ⚡ Pano/Hücre İçi Anomali Erken Uyarı Sistemi

> OG hücreleri ve AG panolarında sıcaklık, akım, nem ve kısmi deşarj gibi belirtileri birlikte izleyip, kritik arıza gerçekleşmeden **önce** risk skoru üreten ve ilgili ekipleri uyarmayı hedefleyen uçtan uca bir izleme prototipi.

**Adm ve Gdz Elektrik Hackathon** (Patika.dev · Grid Up) kapsamında geliştirilmiştir.

---

## 📌 Problem

OG hücreleri ve AG panolardaki arızaların önemli bir bölümü, kritik arıza gerçekleşmeden önce sıcaklık artışı, nem, aşırı akım, izolasyon zayıflığı ve kısmi deşarj (PD) gibi belirtilerle sinyal verir. Ancak mevcut yapılarda bu belirtiler birlikte ve sürekli izlenmediği için problem çoğunlukla ekipman arızası, enerji kesintisi veya yangın riski ortaya çıktıktan **sonra** fark edilir.

## 💡 Çözüm yaklaşımı

Pano içine yerleştirilecek kablosuz, tak-çalıştır bir sensör modülünden gelen verileri merkezi bir sistemde toplayıp, **birden fazla sinyali birlikte değerlendirerek** 0-100 arası bir risk skoru üretiyoruz. Böylece tek bir değerin eşiği aşmasını beklemeden, birlikte yükselen sinyallerden erken uyarı çıkarılabiliyor.

```
[Sensörler] → [Kontrol ünitesi] → [InfluxDB] → [Anomali motoru] → [Dashboard / Alarm / SCADA]
```

Tüm bileşenler **on-premise** çalışacak şekilde tasarlanmıştır; Public Cloud kullanılmaz.

---

## ✅ Mevcut durum

| Bileşen | Durum |
|---|---|
| Sentetik sensör veri üretici (`normal` / `anomaly` modları) | ✅ Çalışıyor |
| InfluxDB ile veri toplama ve saklama | ✅ Çalışıyor |
| Anomali tespit motoru ve risk skoru (`detector.py`) | ✅ Test edildi |
| Grafana monitoring dashboard | 🔧 Kurulum aşamasında |
| Ölçeklenebilirlik testi (50-100 pano) | 🔲 Planlandı |
| Modbus/SCADA haritalama (MPR-53CS register adresleri) | 🔲 Planlandı |
| SMS/WhatsApp alarm bildirimi | 🔲 Planlandı |
| Fiziksel modül konsepti ve elektronik dokümantasyon | 🔲 Planlandı |

---

## 🧠 Anomali tespit mantığı

`detector.py`, veri üreticiden **bağımsız bir süreç** olarak InfluxDB'den okuma yapar ve her pano için risk skoru hesaplar:

- **Eşik puanı:** Sıcaklık, akım, PD ve nem; UYARI / KRİTİK seviyelerine göre puan ekler
- **Birlikte yükselme çarpanı:** Sıcaklık **ve** akım aynı anda yükseliyorsa skor ×1.3 ile artar (tek başına yükselmeden daha tehlikeli kabul edilir)
- **Trend bonusu:** Değerler hızlı tırmanıyorsa, eşik henüz aşılmasa bile skor artar
- **Ark flaşı:** `arc_trip` tetiklendiğinde diğer her şeyi atlayıp anında 100 puan verilir

Gerçek bir çalıştırmada, bir panoda akım ve sıcaklık birlikte UYARI seviyesine girdiğinde skor 15'ten 49'a sıçramış ve seviye NORMAL'den UYARI'ya geçmiştir.

---

## 📐 Gerçek cihaz ve pano verilerine dayanan tasarım

Eşikler ve ölçüm mantığı uydurma değerler yerine, hackathon kapsamında paylaşılan teknik dokümanlara dayanır:

| Konu | Kaynak / Karar |
|---|---|
| Akım ölçümü | CT oranı: 100 mA sekonder = 600 A primer (×6). Ham `secondary_mA` değeri üretilip gerçek akıma çevrilir |
| Akım eşikleri | 1600 kVA AG panonun anma akımı 250-400 A → Normal ≤300 A, Uyarı 300-400 A, Kritik >400 A |
| Kısmi deşarj | Techimp HFCT sensörleri, birim pC (picocoulomb) |
| Ark flaşı | ABB TVOC-2 mantığı: sürekli ölçüm değil, anlık "trip" olayı |
| Nem | TEDAŞ şartnamesine göre +20°C'de %90 bağıl nem normal ortam koşulu; eşikler 70 / 90 |
| Sıcaklık/nem sensörü | SHT31 (I2C) |
| SCADA entegrasyonu | MPR-53CS enerji analizörünün Modbus register haritası referans alınacak |
| Pano ölçüleri | 1600 × 1500 × 450 mm, IP2X, -5°C / +40°C ortam |

---

## 🗂️ Proje yapısı

```
pano-anomali-sistemi/
├── config.py              # Panel listesi, eşikler, CT oranı
├── sensor_simulator.py    # Sentetik sensör verisi üretici
├── detector.py            # Anomali tespit motoru / risk skoru
├── requirements.txt
├── .env.example           # InfluxDB bağlantı şablonu
├── mimari_diyagram.svg    # Uçtan uca sistem mimarisi
├── veriler/               # Örnek akım profili
└── *.md                   # Kapsam, eşik ve cihaz notları
```

---

## 🚀 Kurulum ve çalıştırma

**Gereksinimler:** Python 3.10+, InfluxDB 2.x (OSS). Grafana dashboard için opsiyonel.

```bash
# 1. Sanal ortam ve bağımlılıklar
python -m venv venv
venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt

# 2. InfluxDB bilgilerini ayarla
copy .env.example .env             # ardından .env içindeki INFLUX_TOKEN değerini doldurun

# 3. Veri üreticiyi başlat (bir terminalde)
python sensor_simulator.py --mode anomaly

# 4. Anomali motorunu başlat (ayrı bir terminalde)
python detector.py --interval 5
```

`sensor_simulator.py`, InfluxDB ayarı yoksa veriyi otomatik olarak `data_log.csv` dosyasına yazar.

**Demo senaryosu:** `--mode anomaly` ile seçilen panoda (varsayılan `P-02`) sıcaklık ve akım kademeli olarak yükselir; risk skoru NORMAL → UYARI → KRİTİK geçişini gösterir ve süre sonunda `arc_trip` tetiklenir.

---

## 🛣️ Yol haritası

- [ ] Grafana dashboard (ham veri + risk skoru + alarm listesi)
- [ ] 50-100 panelle ölçeklenebilirlik testi
- [ ] Modbus TCP sunucusu (`pymodbus`) ve register haritalama
- [ ] SMS / WhatsApp alarm mekanizması ve operatör onayı
- [ ] Kabin içi modül konsepti, bileşen listesi ve maliyet tahmini
- [ ] Gerçek 24 saatlik akım profiliyle daha gerçekçi simülasyon

---

## ⚠️ Notlar

- Gerçek saha verisi ve fiziksel sensörlere erişim olmadığından sistem **sentetik veri** üzerinde gösterilmektedir; hackathon şartnamesi buna izin vermektedir.
- Sıcaklık eşikleri makul varsayımlara dayanır; gerçek kurulumda saha verisiyle yeniden kalibre edilmelidir.
- `.env` dosyası token içerdiği için **repoya eklenmemelidir** (`.gitignore` içinde tutun).

## 📄 Lisans

Hackathon projesidir. Lisans bilgisini eklemeden önce yarışma kurallarını kontrol edin.
