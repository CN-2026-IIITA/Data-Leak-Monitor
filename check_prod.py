"""Verify that all API endpoints return session-scoped data."""
import requests, json

BASE = "https://netsentinel-nxv3.onrender.com/api"

print("=" * 60)
print("NetSentinel Data Consistency Audit")
print("=" * 60)

# 1. Stats
print("\n=== /api/stats ===")
r = requests.get(f"{BASE}/stats", timeout=60)
stats = r.json()
for k, v in stats.items():
    print(f"  {k}: {v}")

# 2. Devices
print("\n=== /api/devices ===")
r = requests.get(f"{BASE}/devices", timeout=60)
devices = r.json()
print(f"  Devices returned: {len(devices)}")
for d in devices[:5]:
    print(f"    {d['name']} ({d['mac']}) - {d['status']} - sent:{d['totalBytesSent']} recv:{d['totalBytesReceived']}")

# 3. Traffic count
print("\n=== /api/traffic ===")
r = requests.get(f"{BASE}/traffic?limit=5", timeout=60)
traffic = r.json()
print(f"  Traffic records returned: {len(traffic)}")
if traffic:
    print(f"    Latest: {traffic[0]['timestamp']} -> {traffic[0]['destDomain'] or traffic[0]['destIp']}")

# 4. DNS
print("\n=== /api/dns ===")
r = requests.get(f"{BASE}/dns?limit=5", timeout=60)
dns = r.json()
print(f"  DNS records returned: {len(dns)}")

# 5. Protocols
print("\n=== /api/analytics/protocols ===")
r = requests.get(f"{BASE}/analytics/protocols", timeout=60)
protos = r.json()
for p in protos:
    print(f"  {p['protocol']}: {p['percentage']}%")

# 6. Consistency check
print("\n=== CONSISTENCY CHECK ===")
stat_devices = stats["totalDevices"]
list_devices_count = len(devices)
online_count = sum(1 for d in devices if d["status"] == "online")
print(f"  Stats totalDevices: {stat_devices}")
print(f"  /api/devices count: {list_devices_count}")
print(f"  Stats onlineDevices: {stats['onlineDevices']}")
print(f"  /api/devices online: {online_count}")
match = "PASS" if stat_devices == list_devices_count else "MISMATCH!"
print(f"  Device count match: {match}")
