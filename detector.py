"""
Anomali tespit motoru (Gun 4 gorevi).

InfluxDB'den her panel icin en son verileri okur, esik + trend + "birlikte
yukselme" mantigina gore 0-100 arasi bir risk skoru hesaplar ve sonucu
tekrar InfluxDB'ye ("panel_risk" olcumu) yazar.

sensor_simulator.py'dan BAGIMSIZ calisir: "veri ureten" ile "veriyi analiz
eden" ayri surecler olarak tasarlanmistir - gercek sistemde de boyle olur.

Kullanim:
    python detector.py                 # surekli calisir, InfluxDB'yi izler
    python detector.py --interval 5    # 5 saniyede bir kontrol et
    python detector.py --once          # tek seferlik kontrol (test icin)
"""

import argparse
import json
import os
import time
from datetime import timezone

from config import PANEL_IDS, classify

FIELDS = ["temp_c", "humidity", "current_a", "pd_level", "arc_trip"]


def load_env_file(path=".env"):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def get_influx():
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS

    url = os.environ.get("INFLUX_URL")
    token = os.environ.get("INFLUX_TOKEN")
    org = os.environ.get("INFLUX_ORG")
    bucket = os.environ.get("INFLUX_BUCKET")
    if not all([url, token, org, bucket]):
        raise RuntimeError(
            "InfluxDB ayarlari (.env) bulunamadi. detector.py'in calismasi "
            "icin sensor_simulator.py'in kullandigi ayni .env dosyasi gerekli."
        )
    client = InfluxDBClient(url=url, token=token, org=org)
    return {
        "query_api": client.query_api(),
        "write_api": client.write_api(write_options=SYNCHRONOUS),
        "Point": Point,
        "bucket": bucket,
        "org": org,
    }


def fetch_recent_readings(influx, panel_id: str, lookback: str = "-2m"):
    """Son 'lookback' suredeki tum okumalari zaman sirasiyla dondurur."""
    field_filter = " or ".join(f'r._field == "{f}"' for f in FIELDS)
    flux = f'''
    from(bucket: "{influx['bucket']}")
      |> range(start: {lookback})
      |> filter(fn: (r) => r._measurement == "panel_reading")
      |> filter(fn: (r) => r.panel_id == "{panel_id}")
      |> filter(fn: (r) => {field_filter})
      |> sort(columns: ["_time"])
    '''
    tables = influx["query_api"].query(flux, org=influx["org"])
    by_time = {}
    for table in tables:
        for record in table.records:
            t = record.get_time()
            by_time.setdefault(t, {})[record.get_field()] = record.get_value()
    times_sorted = sorted(by_time.keys())
    return [by_time[t] for t in times_sorted]


def compute_risk(readings: list) -> dict:
    """
    readings: eskiden yeniye siralanmis okuma listesi (dict'ler).
    Donen deger: risk_score (0-100), seviye (NORMAL/UYARI/KRITIK) ve son okuma.
    """
    if not readings:
        return None

    latest = readings[-1]

    # Ark flasi tetiklendiyse baska hicbir hesaba bakmadan aninda KRITIK.
    if bool(latest.get("arc_trip", False)):
        return {"risk_score": 100, "seviye": "KRİTİK", "arc_trip": True, **latest}

    temp_status = classify("temp_c", latest["temp_c"])
    current_status = classify("current_a", latest["current_a"])
    pd_status = classify("pd_level", latest["pd_level"])
    humidity_status = classify("humidity", latest["humidity"])

    score = 0
    score += {"NORMAL": 0, "UYARI": 15, "KRİTİK": 40}[temp_status]
    score += {"NORMAL": 0, "UYARI": 15, "KRİTİK": 40}[current_status]
    score += {"NORMAL": 0, "UYARI": 5, "KRİTİK": 15}[pd_status]
    score += {"NORMAL": 0, "UYARI": 5, "KRİTİK": 10}[humidity_status]

    # "Birlikte degerlendirme": sicaklik VE akim ayni anda yukseliyorsa
    # bu, tek basina yukselmekten daha tehlikelidir -> carpan uygula.
    if temp_status in ("UYARI", "KRİTİK") and current_status in ("UYARI", "KRİTİK"):
        score *= 1.3

    # Trend kontrolu: son birkac olcumde deger ne kadar hizli artmis?
    trend_bonus = 0
    if len(readings) >= 4:
        prev = readings[max(0, len(readings) - 5)]
        if "temp_c" in prev and "current_a" in prev:
            temp_rate = latest["temp_c"] - prev["temp_c"]
            current_rate = latest["current_a"] - prev["current_a"]
            if temp_rate > 5 or current_rate > 30:
                trend_bonus = 10

    score = min(100, round(score + trend_bonus))

    if score >= 70:
        seviye = "KRİTİK"
    elif score >= 30:
        seviye = "UYARI"
    else:
        seviye = "NORMAL"

    return {"risk_score": score, "seviye": seviye, "arc_trip": False, **latest}


def write_risk(influx, panel_id: str, result: dict):
    Point = influx["Point"]
    point = (
        Point("panel_risk")
        .tag("panel_id", panel_id)
        .field("risk_score", result["risk_score"])
        .field("seviye", result["seviye"])
        .field("arc_trip", result["arc_trip"])
        .field("onaylandi", False)  # Gun 6: operator bu alani onaylayacak
    )
    influx["write_api"].write(bucket=influx["bucket"], org=influx["org"], record=point)


def run(interval: float, once: bool):
    load_env_file()
    influx = get_influx()
    print(f"[baslangic] detector.py calisiyor, panels={PANEL_IDS} (durdurmak icin Ctrl+C)")

    try:
        while True:
            for panel_id in PANEL_IDS:
                readings = fetch_recent_readings(influx, panel_id)
                result = compute_risk(readings)
                if result is None:
                    print(f"[uyari] {panel_id} icin henuz veri yok, atlaniyor.")
                    continue
                write_risk(influx, panel_id, result)
                out = {"panel_id": panel_id, **result}
                print(json.dumps(out, ensure_ascii=False, default=str))

            if once:
                break
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[durduruldu] Kullanici tarafindan sonlandirildi.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anomali tespit motoru / risk skoru hesaplayici")
    parser.add_argument("--interval", type=float, default=5.0, help="Kontroller arasi saniye")
    parser.add_argument("--once", action="store_true", help="Tek seferlik calistir (test icin)")
    args = parser.parse_args()

    run(args.interval, args.once)
