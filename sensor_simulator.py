"""
Sentetik sensor veri ureticisi (Gun 2 gorevi).

Gercek sensor yerine, panolardan geliyormus gibi duzenli JSON veri uretir.
Iki modu vardir:
  - normal  : degerler normal aralikta kucuk rastgele dalgalanmalarla akar
  - anomaly : bir panelde sicaklik ve akim kademeli olarak kritik seviyeye tirmanir

Kullanim:
    python sensor_simulator.py                # normal mod, surekli calisir
    python sensor_simulator.py --mode anomaly  # anomaliyi P-02 uzerinde tetikler
    python sensor_simulator.py --interval 2    # 2 saniyede bir olcum uret
    python sensor_simulator.py --duration 60   # 60 saniye sonra dursun (demo icin kullanisli)
"""

import argparse
import csv
import json
import os
import random
import time
from datetime import datetime, timezone

from config import PANEL_IDS, NORMAL_RANGES, ANOMALY_TARGETS, classify, current_from_secondary

CSV_PATH = "data_log.csv"


def try_import_influx():
    """InfluxDB kurulu/ayarlanmis degilse sessizce None doner, script CSV'ye devam eder."""
    try:
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS

        url = os.environ.get("INFLUX_URL")
        token = os.environ.get("INFLUX_TOKEN")
        org = os.environ.get("INFLUX_ORG")
        bucket = os.environ.get("INFLUX_BUCKET")

        if not all([url, token, org, bucket]):
            return None

        client = InfluxDBClient(url=url, token=token, org=org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        return {"write_api": write_api, "bucket": bucket, "org": org, "Point": Point}
    except ImportError:
        return None


def load_env_file(path=".env"):
    """Basit bir .env yukleyici (python-dotenv kurulu degilse diye)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def make_normal_reading():
    """
    Ham CT sekonder degerini (mA) uretir, gercek CT oranina (config.CT_RATIO)
    gore primer akima (current_a) cevirir. Boylece "gercek sensorden okunan
    ham deger -> gercek akim" donusumunu simule ediyoruz.
    """
    secondary_ma = round(random.uniform(*NORMAL_RANGES["secondary_mA"]), 1)
    return {
        "temp_c": round(random.uniform(*NORMAL_RANGES["temp_c"]), 1),
        "humidity": round(random.uniform(*NORMAL_RANGES["humidity"]), 1),
        "secondary_mA": secondary_ma,
        "current_a": current_from_secondary(secondary_ma),
        "pd_level": round(random.uniform(*NORMAL_RANGES["pd_level"]), 1),
        "arc_trip": False,
    }


def make_anomaly_reading(progress: float):
    """
    progress: 0.0 (senaryo basi, hala normale yakin) -> 1.0 (senaryo sonu, kritik)
    Sicaklik ve akimi (CT sekonderi uzerinden) birlikte yukselterek "birlikte
    degerlendirme" senaryosunu simule eder. progress tam 1.0'a ulastiginda
    ABB TVOC-2 benzeri bir ark flasi "trip" olayi da tetiklenir (arc_trip=True).
    """
    base = make_normal_reading()
    base["temp_c"] = round(
        NORMAL_RANGES["temp_c"][1]
        + progress * (ANOMALY_TARGETS["temp_c"] - NORMAL_RANGES["temp_c"][1])
        + random.uniform(-1, 1),
        1,
    )
    secondary_ma = round(
        NORMAL_RANGES["secondary_mA"][1]
        + progress * (ANOMALY_TARGETS["secondary_mA"] - NORMAL_RANGES["secondary_mA"][1])
        + random.uniform(-1, 1),
        1,
    )
    base["secondary_mA"] = secondary_ma
    base["current_a"] = current_from_secondary(secondary_ma)
    base["arc_trip"] = progress >= 1.0
    return base


def write_csv_row(row: dict):
    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def write_influx_row(influx, panel_id: str, reading: dict, timestamp: str):
    Point = influx["Point"]
    point = Point("panel_reading").tag("panel_id", panel_id)
    for k, v in reading.items():
        point = point.field(k, v)
    point = point.time(timestamp)
    influx["write_api"].write(bucket=influx["bucket"], org=influx["org"], record=point)


def run(mode: str, interval: float, duration: float, anomaly_panel: str, anomaly_seconds: float):
    load_env_file()
    influx = try_import_influx()
    if influx:
        print("[bilgi] InfluxDB baglantisi bulundu, veriler InfluxDB'ye yaziliyor.")
    else:
        print(f"[bilgi] InfluxDB bulunamadi/ayarli degil, veriler '{CSV_PATH}' dosyasina yaziliyor.")

    start = time.time()
    elapsed_in_anomaly = 0.0

    print(f"[baslangic] mod={mode} interval={interval}s panels={PANEL_IDS}  (durdurmak icin Ctrl+C)")

    try:
        while True:
            now = time.time()
            if duration and (now - start) >= duration:
                print("[bitti] sure doldu, script durduruluyor.")
                break

            timestamp = datetime.now(timezone.utc).isoformat()

            for panel_id in PANEL_IDS:
                if mode == "anomaly" and panel_id == anomaly_panel:
                    progress = min(elapsed_in_anomaly / anomaly_seconds, 1.0)
                    reading = make_anomaly_reading(progress)
                else:
                    reading = make_normal_reading()

                # Sadece esik tablosu olan metrikleri siniflandir
                # (secondary_mA ham deger, arc_trip ise ayri bir olay tipidir).
                classified_metrics = ["temp_c", "humidity", "current_a", "pd_level"]
                status = {k: classify(k, reading[k]) for k in classified_metrics}
                overall = "KRİTİK" if ("KRİTİK" in status.values() or reading["arc_trip"]) else (
                    "UYARI" if "UYARI" in status.values() else "NORMAL"
                )

                row = {"panel_id": panel_id, "timestamp": timestamp, **reading, "durum": overall}
                print(json.dumps(row, ensure_ascii=False))

                if influx:
                    write_influx_row(influx, panel_id, reading, timestamp)
                else:
                    write_csv_row(row)

            if mode == "anomaly":
                elapsed_in_anomaly += interval

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[durduruldu] Kullanici tarafindan sonlandirildi.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sahte pano sensor verisi ureticisi")
    parser.add_argument("--mode", choices=["normal", "anomaly"], default="normal",
                         help="normal: her sey yolunda | anomaly: bir panelde arizayi tirmandirir")
    parser.add_argument("--interval", type=float, default=3.0, help="Olcumler arasi saniye")
    parser.add_argument("--duration", type=float, default=0,
                         help="Kac saniye calissin (0 = suresiz, Ctrl+C ile durdurun)")
    parser.add_argument("--anomaly-panel", type=str, default="P-02",
                         help="Anomali modunda hangi panel etkilensin")
    parser.add_argument("--anomaly-seconds", type=float, default=60,
                         help="Anomalinin normalden kritige tirmanmasi kac saniye sursun")
    args = parser.parse_args()

    run(args.mode, args.interval, args.duration, args.anomaly_panel, args.anomaly_seconds)
