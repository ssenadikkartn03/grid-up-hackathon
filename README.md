# Pano/Hücre İçi Anomali Erken Uyarı Sistemi — Proje İskeleti

Bu klasör, `solo-8-gun-plani.md` dosyasındaki Gün 1-2 görevlerini yapmaya hazır
başlangıç noktasıdır. Talimatları sırayla takip edin.

---

## Adım 1 — Python ortamını hazırlayın

Bilgisayarınızda Python 3.10+ olduğundan emin olun:
```bash
python3 --version
```
Yoksa: https://www.python.org/downloads/ adresinden indirin (kurulumda
"Add Python to PATH" kutusunu işaretlemeyi unutmayın — Windows'ta).

Bu klasörü bilgisayarınıza indirdikten sonra, klasör içinde bir sanal ortam
oluşturun (kütüphanelerin birbirine karışmaması için):

```bash
cd pano-anomali-sistemi
python3 -m venv venv

# Mac/Linux:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

Sonra gerekli kütüphaneleri kurun:
```bash
pip install -r requirements.txt
```

---

## Adım 2 — InfluxDB kurulumu (zaman serisi veritabanı)

1. https://www.influxdata.com/downloads/ adresinden işletim sisteminize uygun
   **InfluxDB OSS 2.x** sürümünü indirin.
2. Kurulumdan sonra `influxd` komutuyla (veya kurulum sihirbazının açtığı servis
   ile) çalıştırın.
3. Tarayıcıda `http://localhost:8086` adresini açın, ilk kurulum ekranında:
   - Organizasyon adı: `pano-projesi`
   - Bucket adı: `sensor-data`
   - Bir kullanıcı adı/şifre oluşturun
4. **API Token oluşturun:** Sol menüden `Load Data → API Tokens → Generate
   Token → All Access Token`. Bu token'ı kopyalayıp `.env` dosyanıza
   yapıştıracaksınız (aşağıda örnek var).

> Kuruluma vaktiniz yoksa veya sorun yaşarsanız: `sensor_simulator.py` script'i
> InfluxDB olmadan da çalışır, üretilen veriyi ekrana ve bir CSV dosyasına yazar.
> InfluxDB'yi Gün 3'te de kurabilirsiniz.

---

## Adım 3 — Grafana kurulumu (Gün 5'te lazım olacak, şimdiden kurabilirsiniz)

https://grafana.com/grafana/download adresinden işletim sisteminize uygun
sürümü indirin. Kurulumdan sonra `http://localhost:3000` adresinden
(varsayılan kullanıcı/şifre: `admin`/`admin`) giriş yapabilirsiniz.

---

## Adım 4 — (Opsiyonel) Mosquitto MQTT broker

Gerçekçi bir "sensör → broker → veritabanı" akışı göstermek isterseniz:
https://mosquitto.org/download/ adresinden kurun. Zaman darsa bu adımı
atlayıp script'ten doğrudan InfluxDB'ye yazabilirsiniz — planda da belirtildiği
gibi bu tamamen kabul edilebilir bir basitleştirme.

---

## Adım 5 — Ortam değişkenlerini ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın ve kendi InfluxDB
bilgilerinizi girin:
```bash
cp .env.example .env
```

---

## Adım 6 — Sentetik veri üreticiyi çalıştırın

```bash
# Normal mod (varsayılan):
python sensor_simulator.py

# Anomali senaryosunu tetiklemek için:
python sensor_simulator.py --mode anomaly
```

Script çalıştığında hem terminalde veriyi göreceksiniz hem de (InfluxDB
bağlantısı `.env` içinde tanımlıysa) veriler InfluxDB'ye yazılacak; tanımlı
değilse otomatik olarak `data_log.csv` dosyasına yazılır.

---

## Klasördeki dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `config.py` | Panel listesi + Gün 1'deki eşik tablosu (tek yerden yönetilir) |
| `sensor_simulator.py` | Gün 2 görevi: sahte sensör verisi üretici (normal/anomali modları) |
| `requirements.txt` | Gerekli Python kütüphaneleri |
| `.env.example` | InfluxDB bağlantı bilgileri şablonu |
| `kapsam_ve_esik_notu.md` | Gün 1 çıktısı: kapsam kararı ve eşik tablosu (jüri/dokümantasyon için) |

## Sırada ne var?

Bu iskelet Gün 1-2'yi kapsıyor. Gün 3'e geçtiğinizde (`influx_writer.py` gibi
bir dosya ile) `sensor_simulator.py`'ın ürettiği veriyi düzenli olarak
InfluxDB'ye yazan kısmı birlikte yazabiliriz — o zaman bana haber verin.
