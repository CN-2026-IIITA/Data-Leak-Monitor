"""
Direct Anomaly Injection Script for NetSentinel
================================================
This script BYPASSES the sniffer entirely and sends crafted malicious-looking
traffic records directly to the Cloud Backend's /api/ingest endpoint.
The backend's rules engine will then evaluate these records and generate alerts.

Usage: python inject_anomalies.py
"""

import requests
import json
import uuid
import time
import gzip

CLOUD_API_URL = "https://netsentinel-nxv3.onrender.com/api/ingest"
API_KEY = "agent-686aa6f9-4e00-4f4f-8fe0-9ae4a8e0c86d"

DEVICE_MAC = "c0:35:32:38:13:81"  # ByteKnight - your laptop
DEVICE_IP = "10.206.89.243"

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def send_payload(payload, label):
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
        "Content-Encoding": "gzip",
        "X-Message-ID": str(uuid.uuid4())
    }
    compressed = gzip.compress(json.dumps(payload).encode("utf-8"))
    try:
        res = requests.post(CLOUD_API_URL, data=compressed, headers=headers, timeout=30)
        print(f"  [{label}] HTTP {res.status_code}: {res.text[:200]}")
        return res.status_code == 200
    except Exception as e:
        print(f"  [{label}] FAILED: {e}")
        return False

def main():
    print("=" * 60)
    print("NetSentinel Direct Anomaly Injection")
    print("=" * 60)
    print()

    # 1. TRACKER: Contact known tracking domain
    print("[1/5] Injecting TRACKER activity (google-analytics.com)...")
    send_payload({
        "devices": [{"mac": DEVICE_MAC, "ip": DEVICE_IP, "type": "laptop", "hostname": "ByteKnight", "hostname_source": "system", "status": "online", "ip_history": [DEVICE_IP]}],
        "traffic_records": [{
            "id": f"test-tracker-{uuid.uuid4().hex[:8]}",
            "timestamp_start": now_iso(), "timestamp_end": now_iso(),
            "src_ip": DEVICE_IP, "dest_ip": "142.250.80.46",
            "src_mac": DEVICE_MAC, "dest_mac": "82:72:e5:38:87:2d",
            "device_mac": DEVICE_MAC,
            "direction": "outbound", "protocol": "TCP",
            "src_port": 54321, "dest_port": 443,
            "bytes": 2048, "packets": 5, "tcp_flags_seen": 0, "min_ttl": 64,
            "domain": "google-analytics.com", "domain_source": "sni",
        }],
        "alerts": [], "anomalies": []
    }, "Tracker")
    time.sleep(1)

    # 2. UNKNOWN DOMAIN: First-time connection to suspicious domain
    print("[2/5] Injecting UNKNOWN DOMAIN (suspicious-c2-server.xyz)...")
    send_payload({
        "devices": [],
        "traffic_records": [{
            "id": f"test-unknown-{uuid.uuid4().hex[:8]}",
            "timestamp_start": now_iso(), "timestamp_end": now_iso(),
            "src_ip": DEVICE_IP, "dest_ip": "185.220.101.33",
            "src_mac": DEVICE_MAC, "dest_mac": "82:72:e5:38:87:2d",
            "device_mac": DEVICE_MAC,
            "direction": "outbound", "protocol": "TCP",
            "src_port": 49999, "dest_port": 443,
            "bytes": 4096, "packets": 8, "tcp_flags_seen": 0, "min_ttl": 64,
            "domain": "suspicious-c2-server.xyz", "domain_source": "sni",
        }],
        "alerts": [], "anomalies": []
    }, "Unknown Domain")
    time.sleep(1)

    # 3. GEO ANOMALY: Traffic to Russia  
    print("[3/5] Injecting GEO ANOMALY (connection to Russia 77.88.55.60 / yandex.ru)...")
    send_payload({
        "devices": [],
        "traffic_records": [{
            "id": f"test-geo-{uuid.uuid4().hex[:8]}",
            "timestamp_start": now_iso(), "timestamp_end": now_iso(),
            "src_ip": DEVICE_IP, "dest_ip": "77.88.55.60",
            "src_mac": DEVICE_MAC, "dest_mac": "82:72:e5:38:87:2d",
            "device_mac": DEVICE_MAC,
            "direction": "outbound", "protocol": "TCP",
            "src_port": 55555, "dest_port": 443,
            "bytes": 3072, "packets": 6, "tcp_flags_seen": 0, "min_ttl": 64,
            "domain": "yandex.ru", "domain_source": "sni",
            "dest_country": "RU",
        }],
        "alerts": [], "anomalies": []
    }, "Geo Anomaly")
    time.sleep(1)

    # 4. COMBINED HIGH SCORE: Tracker + Unknown + Foreign = Score 6 (HIGH)
    print("[4/5] Injecting HIGH SEVERITY combo (tracker + unknown + foreign)...")
    send_payload({
        "devices": [],
        "traffic_records": [{
            "id": f"test-high-{uuid.uuid4().hex[:8]}",
            "timestamp_start": now_iso(), "timestamp_end": now_iso(),
            "src_ip": DEVICE_IP, "dest_ip": "103.224.182.251",
            "src_mac": DEVICE_MAC, "dest_mac": "82:72:e5:38:87:2d",
            "device_mac": DEVICE_MAC,
            "direction": "outbound", "protocol": "TCP",
            "src_port": 60000, "dest_port": 80,
            "bytes": 1048576, "packets": 200, "tcp_flags_seen": 0, "min_ttl": 32,
            "domain": "telemetry.microsoft.com", "domain_source": "sni",
            "dest_country": "CN",
        }],
        "alerts": [], "anomalies": []
    }, "High Severity Combo")
    time.sleep(1)

    # 5. TRAFFIC SPIKE: Huge data transfer
    print("[5/5] Injecting TRAFFIC SPIKE (50MB burst)...")
    send_payload({
        "devices": [],
        "traffic_records": [{
            "id": f"test-spike-{uuid.uuid4().hex[:8]}",
            "timestamp_start": now_iso(), "timestamp_end": now_iso(),
            "src_ip": DEVICE_IP, "dest_ip": "104.26.10.78",
            "src_mac": DEVICE_MAC, "dest_mac": "82:72:e5:38:87:2d",
            "device_mac": DEVICE_MAC,
            "direction": "outbound", "protocol": "TCP",
            "src_port": 61000, "dest_port": 443,
            "bytes": 52428800, "packets": 5000, "tcp_flags_seen": 0, "min_ttl": 64,
            "domain": "unknown-upload-server.io", "domain_source": "sni",
        }],
        "alerts": [], "anomalies": []
    }, "Traffic Spike")

    print()
    print("=" * 60)
    print("Injection complete! Waiting 10s for background processing...")
    print("=" * 60)
    time.sleep(10)

    # Verify results
    print()
    print("Checking results...")
    r = requests.get("https://netsentinel-nxv3.onrender.com/api/alerts", timeout=30)
    alerts = r.json()
    print(f"Alerts: {len(alerts.get('data', []))}")
    for a in alerts.get('data', []):
        print(f"  [{a['severity']}] {a['title']}")

    r = requests.get("https://netsentinel-nxv3.onrender.com/api/anomalies", timeout=30)
    anoms = r.json()
    print(f"Anomalies: {len(anoms)}")
    for a in anoms:
        print(f"  [{a['severity']}] {a['description'][:80]}")

    if not alerts.get('data') and not anoms:
        print()
        print("WARNING: No alerts detected. The Render backend may still be deploying.")
        print("Check Render dashboard: https://dashboard.render.com")

if __name__ == "__main__":
    main()
