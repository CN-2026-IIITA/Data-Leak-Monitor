import requests
import time
import socket
import threading
import uuid

print("==============================================")
print(" NetSentinel E2E Anomaly Generation Test Script")
print("==============================================")
print("Keep your local NetSentinel agent (sniffer.py) running in the background.")
print("This script will generate real network traffic designed to trigger the detection engine.")
print()

def trigger_tracker():
    print("[1] Generating Tracker / Telemetry Activity (+1 Score)")
    try:
        # Pinging known tracking domains defined in tracker_list.py
        trackers = [
            "https://www.google-analytics.com",
            "https://telemetry.microsoft.com",
            "https://pixel.facebook.com"
        ]
        for url in trackers:
            print(f"    -> Contacting {url}")
            try:
                requests.get(url, timeout=3)
            except Exception:
                pass # Expected to fail or timeout sometimes, the DNS/TCP connection is what the sniffer sees
        print("    -> Done. The sniffer should log tracker activity.\n")
    except Exception as e:
        print(f"    -> Error: {e}")

def trigger_unknown_domain():
    print("[2] Generating Unknown/New External Connection (+3 Score)")
    try:
        # Contacting a completely randomized domain that has never been seen
        random_domain = f"http://{uuid.uuid4().hex[:12]}.com"
        print(f"    -> Contacting completely unknown domain: {random_domain}")
        try:
            requests.get(random_domain, timeout=3)
        except Exception:
            pass # DNS will fail, but the DNS query itself is picked up by the sniffer!
        print("    -> Done. The sniffer should log an unknown connection attempt.\n")
    except Exception as e:
        print(f"    -> Error: {e}")

def trigger_geo_anomaly():
    print("[3] Generating Geo-Anomaly (+2 Score)")
    print("    -> Connecting to servers hosted in unexpected countries (Russia/China) to trigger geographic alerts.")
    foreign_sites = [
        "https://www.yandex.ru", # Russia
        "https://www.baidu.com", # China
        "http://www.gov.za"      # South Africa
    ]
    for url in foreign_sites:
        print(f"    -> Contacting {url}")
        try:
            requests.get(url, timeout=3)
        except Exception:
            pass
    print("    -> Done. The backend will map these IPs to foreign countries and alert.\n")

def trigger_traffic_spike():
    print("[4] Generating Traffic Spike (+2 Score)")
    print("    -> Downloading a large test file to exceed the baseline average bytes/hour.")
    try:
        # Download a 10MB test file from an internet speed test server
        url = "http://speedtest.tele2.net/10MB.zip"
        print(f"    -> Downloading 10MB from {url}...")
        res = requests.get(url, stream=True, timeout=10)
        downloaded = 0
        for chunk in res.iter_content(chunk_size=1024*1024):
            if chunk:
                downloaded += len(chunk)
                print(f"       ... {downloaded // (1024*1024)} MB downloaded")
        print("    -> Done. This should trigger a traffic spike anomaly.\n")
    except Exception as e:
        print(f"    -> Note: Download failed or timed out ({e}). The attempt alone might generate enough traffic.\n")

def run_all():
    trigger_tracker()
    time.sleep(2)
    trigger_unknown_domain()
    time.sleep(2)
    trigger_geo_anomaly()
    time.sleep(2)
    trigger_traffic_spike()
    
    print("==============================================")
    print("Test Complete!")
    print("Please check your NetSentinel Dashboard (Alerts & AI Detection panels).")
    print("You should see Medium to High severity alerts generated for this device.")
    print("Note: The background processing runs periodically, so it may take 10-30 seconds to appear.")

if __name__ == "__main__":
    run_all()
