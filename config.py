"""
Proje genelinde kullanılacak sabitler.

GUNCELLEME (gercek_cihaz_notlari.md sonrasi): Bu dosyadaki esikler artik
organizatorlerin paylastigi GERCEK cihaz/pano verilerine dayanmaktadir:
  - Akim: 1600 kVA panonun TEDAS sartnamesindeki gercek CT orani (2500/5)
    ve anma akimi (250-400A) baz alinmistir.
  - Akim olcum mantigi: gercek CT sekonderi 100mA / primeri 600A oranindan
    (Iistenen Veriler.xlsx -> "Akim Sensoru" sayfasi) esitlenen carpan.
  - PD (kismi desarj): Techimp HFCT sensor datasheet'ine gore birim pC
    (picocoulomb) olarak degistirildi (eskiden 0-1 arasi uydurma birimdi).

Sonraki gunlerde (detector.py, dashboard sorgulari vb.) bu dosyadan import
edilir, boylece esikler tek yerden yonetilir.
"""

# İzlenecek sahte panolar (ölçeklenebilirlik izlenimi için 3 tane)
PANEL_IDS = ["P-01", "P-02", "P-03"]

# GERÇEK CT (akım trafosu) oranı: sekonder mA * CT_RATIO = primer Amper
# Kaynak: Iistenen Veriler.xlsx -> "Akım Sensörü" sayfası
# (Sekonder 100 mA = Primer 600 A -> 600/100 = 6)
CT_RATIO = 6

# Gün 1 eşik tablosu (current_a ve pd_level artık gerçek verilere göre
# güncellendi): (normal_max, uyari_max) -> bunun üstü KRİTİK
THRESHOLDS = {
    "temp_c": {"normal_max": 45, "uyari_max": 60},
    # TEDAS sartnamesi: dahili ortamda +20C'de %90 bagil nem NORMAL kabul edilir.
    "humidity": {"normal_max": 70, "uyari_max": 90},
    # 1600 kVA panonun TEDAŞ şartnamesindeki anma akımı 250-400A'dır.
    "current_a": {"normal_max": 300, "uyari_max": 400},
    # Techimp HFCT datasheet'ine göre pC (picocoulomb) birimi.
    # Bu ilk kalibrasyon değerleridir; gerçek kurulumda saha verisiyle
    # (arka plan PD gürültü seviyesi ölçülerek) yeniden kalibre edilir.
    "pd_level": {"normal_max": 50, "uyari_max": 150},
}

# Normal koşullarda değerlerin dalgalanacağı aralıklar (sensor_simulator.py kullanır)
NORMAL_RANGES = {
    "temp_c": (20, 40),
    "humidity": (30, 55),
    # Ham sensör çıktısı burada: 0-100mA aralığındaki CT sekonder akımı.
    # current_a bundan CT_RATIO ile hesaplanır (bkz. sensor_simulator.py).
    "secondary_mA": (15, 50),   # -> yaklaşık 90-300 A (NORMAL bandı)
    "pd_level": (5, 40),        # pC, arka plan gürültü seviyesi
}

# Anomali senaryosunda hedeflenecek "kritik" değerler
ANOMALY_TARGETS = {
    "temp_c": 68,
    "humidity": 55,        # anomali senaryosunda nemi sabit bırakıyoruz
    "secondary_mA": 90,    # -> 540 A, KRİTİK eşiğin (400A) üzerinde
    "pd_level": 40,        # PD'yi bu senaryoda değiştirmiyoruz (ayrı bir senaryo)
}


def current_from_secondary(secondary_ma: float) -> float:
    """Ham CT sekonder değerini (mA) gerçek primer akıma (A) çevirir."""
    return round(secondary_ma * CT_RATIO, 1)


def classify(metric: str, value: float) -> str:
    """Bir ölçüm değerini NORMAL / UYARI / KRİTİK olarak etiketler."""
    t = THRESHOLDS[metric]
    if value <= t["normal_max"]:
        return "NORMAL"
    elif value <= t["uyari_max"]:
        return "UYARI"
    else:
        return "KRİTİK"
