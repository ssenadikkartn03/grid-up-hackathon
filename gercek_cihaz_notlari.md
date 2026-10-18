# Organizatörlerden Gelen Gerçek Veri/Cihaz Notları

Bu doküman, hackathon ekibinin paylaştığı zip içindeki gerçek cihaz teknik
verilerinin projemiz için ne anlama geldiğini özetler. Artık uydurma
değerler yerine, bu gerçek özelliklere dayanan bir sistem kurabilirsiniz —
bu, "sahaya uygulanabilirlik" ve "gerçekçilik" açısından jüride fark yaratır.

---

## 1. Akım Sensörü — GERÇEK ölçüm mantığı ve örnek veri seti

Organizatörler size **gerçek bir CT (akım trafosu) ölçüm formülü** ve
**24 saatlik örnek bir akım profili** vermiş (`Iistenen Veriler.xlsx` →
"Akım Sensörü" sayfası).

**Gerçek mantık:**
- Kullanılan CT'nin sekonderi **100 mA**, primeri (gerçek şebeke akımı) **600 A**
- Yani oran: **600A / 100mA = 6000** (bu değer sayfada "Çarpan" olarak geçiyor)
- Formül: `Primer Akım (A) = Sekonder Değer (mA) × 6000 / 1000` yani
  pratikte **sekonder mA değerini 6 ile çarpmanız yeterli**
- Örnek: sensör 53 mA okursa → gerçek akım 53 × 6 = 318 A

Bu, projenizde "akım sensöründen okunan ham değer → gerçek akım" dönüşümünü
gerçekçi şekilde göstermenizi sağlıyor. `sensor_simulator.py`'da artık
doğrudan "current_a" üretmek yerine, önce ham "sekonder_mA" (0-100 mA)
üretip sonra ×6 ile "current_a"ya çevirebilirsiniz — bu, jüriye "biz gerçek
sensör davranışını simüle ettik" demenizi sağlar.

**24 saatlik örnek profil:** `veriler/akim_l1_ornek_profil.csv` dosyasına
çıkardım (15 dakikalık aralıklarla, 152 satır). İsterseniz bunu tamamen
rastgele veri yerine "gerçekçi günlük yük eğrisi" olarak simülatörünüze
temel alabilirsiniz (ör. gece düşük, gündüz daha değişken yük).

---

## 2. Ark Flaşı Sensörü — GERÇEK cihaz: ABB TVOC-2 (Arc Guard System)

Şartname bunu "Ark flaşlarının izlenmesi" olarak istiyordu; organizatörler
**gerçek bir endüstriyel ürünün** (ABB TVOC-2) Modbus kılavuzunu vermiş.

**Önemli teknik bilgiler:**
- Cihaz Modbus RTU üzerinden **slave** olarak çalışıyor (yani bir merkezi
  sistem/PLC bu cihazdan register okuyor — tam sizin mimarinize uygun)
- **Trip (tetiklenme) register'ları** şu şekilde: `Trip 1 detector` (adres
  100/0x64), `Trip 1 relay` (adres 102), `Trip 1 date/time` (adres 103-105).
  Cihaz aynı mantıkla Trip 2, Trip 3... diye 7 ayrı tetiklenme kaydı tutuyor.
- Pratik anlamı: **ark flaşı sürekli ölçülen bir değer değil, "tetiklendi/
  tetiklenmedi" (trip) olayıdır** — tıpkı planımızdaki "anlık kritik olay"
  yaklaşımıyla birebir örtüşüyor.

Projenizde: Modbus haritalama tablonuza gerçek bir satır olarak
`Trip 1 detector — Adres 100 (0x64) — ABB TVOC-2 (gerçek cihaz)` eklemeniz,
jüriye "biz gerçek bir endüstriyel cihazın protokolünü referans aldık"
izlenimini verir.

---

## 3. Kısmi Deşarj (PD) Sensörü — GERÇEK cihaz: Techimp HFCT (30mm/50mm)

**Teknik özellikler:**
- HFCT (High Frequency Current Transformer) — kablonun toprak bağlantısına
  takılan, indüktif bir sensör, **bakım gerektirmez** (şartnamenin istediği
  "tak-çalıştır" özelliğiyle birebir uyumlu)
- Bant genişliği: 1-60 MHz
- Çıkış sinyali PD şiddetiyle orantılı (**birim: pC — picocoulomb**),
  50Hz'te 100A karşılığı 0,6Vpp, PD frekansında 100pC karşılığı 0,4Vpp
- Çalışma sıcaklığı: -20°C ile +70°C (kabin içi sıcaklık dalgalanmalarına
  dayanıklı, bu da tasarım notunuzda işinize yarar)

**Önemli fark:** Bu sensör doğrudan dijital/Modbus çıkışı vermiyor — analog
bir gerilim sinyali üretiyor, bunu okumak için ayrı bir "PD analizör
ünitesi" gerekiyor. Yani mimarinizde: `HFCT sensör → analog sinyal → PD
analiz kartı → dijital veri (pC cinsinden) → merkezi sistem` şeklinde bir
ek katman olduğunu belirtmeniz gerçekçilik katar.

Önerim: `config.py`'daki `pd_level` alanını 0-1 yerine **pC** birimine
çevirin (ör. normal <50 pC, uyarı 50-150 pC, kritik >150 pC) — bunlar örnek
değerlerdir, gerçek kalibrasyon saha koşuluna göre yapılır demeniz yeterli.

---

## 4. Modbus Haritalama için GERÇEK referans cihaz: MPR-53CS (enerji analizörü)

Bu, çok değerli bir bulgu: organizatörler size **gerçek bir 3 fazlı enerji
analizörünün tam Modbus register haritasını** vermiş. Gün 6'daki "kendi
uydurduğumuz register adresleri" yerine, **gerçek ve profesyonel bir
cihazın adreslerini** kullanabilirsiniz — bu Modbus/SCADA entegrasyon
kısmında büyük bir güvenilirlik katar.

Öne çıkan gerçek register'lar (PDU adresleri, decimal):

| Veri | Adres (Dec) | Adres (Hex) | Birim | Çarpan |
|---|---|---|---|---|
| L1 Faz Akımı | 6 | 0x0006 | Amper | 0.001 |
| L2 Faz Akımı | 8 | 0x0008 | Amper | 0.001 |
| L3 Faz Akımı | 10 | 0x000A | Amper | 0.001 |
| L1 Faz Gerilimi | 0 | 0x0000 | Volt | 0.1 |
| Frekans | 58 | 0x003A | Hz | 0.01 |
| L1 Faz Aktif Güç | 20 | 0x0014 | Watt | 0.1 |

Gün 6'da `pymodbus` ile kuracağınız simülasyon sunucusunda, kendi
uydurduğunuz `40001, 40002...` yerine **bu gerçek adresleri** kullanabilir
ve "MPR-53CS uyumlu register haritalaması" diyebilirsiniz — bu, jüriye
mevcut SCADA altyapılarıyla gerçekten uyumlu olduğunuzu gösterir.

---

## 5. 1600 kVA AG Pano — gerçek elektriksel büyüklükler

TEDAŞ-MLZ/2003-06.B şartnamesinden (paylaşılan PDF):

| Özellik | Değer |
|---|---|
| Ana bara kesiti | 2×(100×10 mm²) |
| Ana akım trafosu oranı | 2500/5 |
| Anma akımı | 250-400 A |

Bu, `config.py`'daki akım eşiklerinizi (şu an 150/180A) **gerçek panoya
göre güncellemeniz gerektiği** anlamına gelir. Örneğin:
- Normal: ≤ 300 A
- Uyarı: 300-400 A (anma akımına yaklaşma)
- Kritik: > 400 A (anma akımını aşma)

Bu değerleri sunumda "1600 kVA panonun TEDAŞ şartnamesindeki anma
akımına göre kalibre edildi" diyerek gerekçelendirebilirsiniz — bu, jürinin
"problemi doğru anlama" kriterinde büyük puan getirir.

---

## Önerilen aksiyon: config.py'ı güncelleyelim mi?

Yukarıdaki gerçek verilere göre `config.py` dosyasındaki eşikleri ve
birimleri güncellemek ister misiniz? İsterseniz hemen düzenleyip size
güncel dosyayı verebilirim.
