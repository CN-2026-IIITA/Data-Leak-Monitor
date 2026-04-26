import threading
import time
import requests
import os
import sqlite3
import logging
import json
import uuid
import re
import ipaddress
from collections import OrderedDict
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import gzip
import random
import socket

from scapy.all import sniff, IP, IPv6, TCP, UDP, ARP, DHCP, Ether, DNS, DNSQR, Raw, conf

# Setup Agent Logging
if not os.path.exists("logs"):
    os.makedirs("logs")
logger = logging.getLogger("local_agent")
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler("logs/local_agent.log", maxBytes=5*1024*1024, backupCount=2)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(file_formatter)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

from dotenv import load_dotenv
load_dotenv()

CLOUD_API_URL = os.getenv("CLOUD_API_URL", "http://127.0.0.1:8000/api/ingest")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "insert-api-key-here")

# --- Helpers ---
def is_randomized_mac(mac):
    if not mac or len(mac) < 17: return False
    try:
        first_byte = int(mac[0:2], 16)
        return bool(first_byte & 0x02)
    except: return False

def get_direction(src_ip, dest_ip):
    try:
        src_priv = ipaddress.ip_address(src_ip).is_private
        dst_priv = ipaddress.ip_address(dest_ip).is_private
        if src_priv and dst_priv: return "lateral"
        if src_priv and not dst_priv: return "outbound"
        if dst_priv and not src_priv: return "inbound"
        return "external"
    except: return "unknown"

def extract_sni(payload):
    if len(payload) > 40 and payload[0] == 0x16 and payload[5] == 0x01:
        idx = payload.find(b'\x00\x00')
        if idx != -1 and idx + 9 < len(payload):
            sni_chunk = payload[idx+4:idx+64]
            m = re.search(br'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', sni_chunk)
            if m: return m.group(0).decode('utf-8', errors='ignore')
    return None

def _get_local_mac():
    """Get this machine's MAC address from its active network interface."""
    try:
        from scapy.all import get_working_ifaces
        for iface in get_working_ifaces():
            if iface.ip and not iface.ip.startswith("127.") and not iface.ip.startswith("169.254"):
                if hasattr(iface, 'mac') and iface.mac:
                    return iface.mac.lower()
    except Exception:
        pass
    # Fallback using uuid
    mac_int = uuid.getnode()
    return ':'.join(('%012x' % mac_int)[i:i+2] for i in range(0, 12, 2))

def _get_local_ip():
    """Get this machine's primary local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def _get_hostname():
    """Get this machine's hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return "Unknown"


class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity
    def get(self, key):
        if key not in self.cache: return None
        self.cache.move_to_end(key)
        return self.cache[key]
    def put(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class PacketSniffer:
    def __init__(self):
        self.is_running = False
        self.lock = threading.Lock()
        self.db_lock = threading.Lock()  # Dedicated lock for all SQLite operations
        
        # Discover this machine's identity at startup
        self.local_mac = _get_local_mac()
        self.local_ip = _get_local_ip()
        self.local_hostname = _get_hostname()
        
        # In-Memory Stores
        self.devices = {} # mac -> dict
        self.ip_to_mac = {}
        self.flow_cache = LRUCache(10000) # Max 10k flows
        self.dns_cache = LRUCache(5000) # IP -> domain
        
        # Pre-register this machine as a device
        self.devices[self.local_mac] = {
            "mac": self.local_mac, "ip": self.local_ip, "ip_history": {self.local_ip},
            "hostname": self.local_hostname, "hostname_source": "system",
            "is_randomized_mac": is_randomized_mac(self.local_mac),
            "type": "laptop", "vendor": "Local Machine"
        }
        self.ip_to_mac[self.local_ip] = self.local_mac
        
        # Counters for logging
        self._packets_captured = 0
        self._flows_flushed = 0
        self._messages_sent = 0
        
        # SQLite Outbox Buffer — initialize in a thread-safe way
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database."""
        with self.db_lock:
            self.db_conn = sqlite3.connect("agent_cache.db", check_same_thread=False)
            self.db_conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
            self.db_conn.execute('''CREATE TABLE IF NOT EXISTS outbox_queue (
                                      id TEXT PRIMARY KEY,
                                      payload TEXT,
                                      status TEXT,
                                      retry_count INTEGER DEFAULT 0,
                                      next_retry REAL DEFAULT 0
                                   )''')
            self.db_conn.commit()

    def _db_execute(self, query, params=(), fetch=False, fetchone=False):
        """Thread-safe SQLite execution. Creates a new cursor each call."""
        with self.db_lock:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                if fetchone:
                    return cursor.fetchone()
                self.db_conn.commit()
                return None
            except Exception as e:
                logger.error(f"DB error: {e}")
                return [] if fetch else None

    def start(self):
        if not self.is_running:
            self.is_running = True
            logger.info(f"Local machine: {self.local_hostname} ({self.local_ip}) MAC={self.local_mac}")
            threading.Thread(target=self._sniff_loop, daemon=True).start()
            threading.Thread(target=self._flush_loop, daemon=True).start()
            threading.Thread(target=self._sender_loop, daemon=True).start()
            threading.Thread(target=self._stats_loop, daemon=True).start()
            return True
        return False

    def stop(self):
        self.is_running = False

    def _update_device(self, mac, ip, hostname=None, hostname_source="unknown"):
        if not mac or mac == "ff:ff:ff:ff:ff:ff": return
        mac = mac.lower()
        with self.lock:
            if ip: self.ip_to_mac[ip] = mac
            if mac not in self.devices:
                self.devices[mac] = {
                    "mac": mac, "ip": ip, "ip_history": set(),
                    "hostname": hostname, "hostname_source": hostname_source,
                    "is_randomized_mac": is_randomized_mac(mac),
                    "type": "unknown", "vendor": "Unknown"
                }
            dev = self.devices[mac]
            if ip:
                dev["ip"] = ip
                dev["ip_history"].add(ip)
            if hostname and dev["hostname_source"] != "manual":
                dev["hostname"] = hostname
                dev["hostname_source"] = hostname_source

    def _process_packet(self, packet):
        self._packets_captured += 1
        
        # 1. Passive Device Discovery
        if Ether in packet:
            src_mac = packet[Ether].src
            if ARP in packet:
                self._update_device(src_mac, packet[ARP].psrc)
            elif DHCP in packet:
                # Extract hostname from DHCP options
                hostname = None
                for opt in packet[DHCP].options:
                    if isinstance(opt, tuple) and opt[0] == 'hostname':
                        hostname = opt[1].decode('utf-8', errors='ignore')
                        break
                if IP in packet:
                    self._update_device(src_mac, packet[IP].src, hostname, "dhcp")
        
        # 2. DPI & Flow Tracking
        is_ipv4 = IP in packet
        is_ipv6 = IPv6 in packet
        if not (is_ipv4 or is_ipv6): return
        
        layer_ip = packet[IP] if is_ipv4 else packet[IPv6]
        src_ip = layer_ip.src
        dst_ip = layer_ip.dst
        ttl = layer_ip.ttl if is_ipv4 else layer_ip.hlim
        bytes_len = len(packet)
        
        protocol = "Unknown"
        src_port, dst_port = 0, 0
        tcp_flags = 0
        
        domain = None
        domain_source = "unknown"
        
        if TCP in packet:
            protocol = "TCP"
            src_port, dst_port = packet[TCP].sport, packet[TCP].dport
            tcp_flags = int(packet[TCP].flags)
            if Raw in packet:
                sni = extract_sni(packet[Raw].load)
                if sni:
                    domain = sni
                    domain_source = "sni"
                    with self.lock: self.dns_cache.put(dst_ip, domain)
        elif UDP in packet:
            protocol = "UDP"
            src_port, dst_port = packet[UDP].sport, packet[UDP].dport
            if dst_port == 53 or src_port == 53:
                if DNS in packet and packet[DNS].qr == 0 and packet[DNS].qdcount > 0:
                    try:
                        domain = packet[DNSQR].qname.decode('utf-8', errors='ignore').rstrip('.')
                        domain_source = "dns"
                        with self.lock: self.dns_cache.put(dst_ip, domain)
                    except: pass
        
        # Resolve domain from cache if not found
        if not domain:
            with self.lock:
                cached = self.dns_cache.get(dst_ip)
                if cached:
                    domain = cached
                    domain_source = "dns_cache"

        # Determine device_mac: use Ether src first, then IP->MAC table, then fallback to local
        device_mac = None
        if Ether in packet:
            src_mac_raw = packet[Ether].src.lower()
            # If this packet's src MAC is a device we know, use it
            with self.lock:
                if src_mac_raw in self.devices:
                    device_mac = src_mac_raw
        
        if not device_mac:
            with self.lock:
                device_mac = self.ip_to_mac.get(src_ip)
        
        # Fallback: if src_ip is our local IP, attribute to our own MAC
        if not device_mac:
            try:
                if ipaddress.ip_address(src_ip).is_private:
                    device_mac = self.local_mac
            except Exception:
                pass

        # Update Flow Cache
        flow_key = (src_ip, dst_ip, src_port, dst_port, protocol)
        with self.lock:
            flow = self.flow_cache.get(flow_key)
            now = datetime.now(timezone.utc).isoformat()
            if not flow:
                src_mac_val = packet[Ether].src if Ether in packet else None
                dst_mac_val = packet[Ether].dst if Ether in packet else None
                
                flow = {
                    "timestamp_start": now,
                    "timestamp_end": now,
                    "src_ip": src_ip, "dest_ip": dst_ip,
                    "src_mac": src_mac_val, "dest_mac": dst_mac_val,
                    "device_mac": device_mac,
                    "direction": get_direction(src_ip, dst_ip),
                    "protocol": protocol, "src_port": src_port, "dest_port": dst_port,
                    "bytes": 0, "packets": 0, "tcp_flags_seen": 0, "min_ttl": ttl,
                    "domain": domain, "domain_source": domain_source
                }
                self.flow_cache.put(flow_key, flow)
            
            flow["timestamp_end"] = now
            flow["bytes"] += bytes_len
            flow["packets"] += 1
            flow["tcp_flags_seen"] |= tcp_flags
            if ttl < flow["min_ttl"]: flow["min_ttl"] = ttl
            if domain and flow["domain_source"] in ["unknown", "dns_cache"]:
                flow["domain"] = domain
                flow["domain_source"] = domain_source

    def _flush_loop(self):
        """Periodically flushes in-memory flows to SQLite outbox."""
        while self.is_running:
            time.sleep(5)
            with self.lock:
                flows_to_flush = list(self.flow_cache.cache.values())
                self.flow_cache.cache.clear()
            
            if not flows_to_flush: continue
            
            # Format and save to outbox
            for flow in flows_to_flush:
                flow["id"] = str(uuid.uuid4())
            
            self._flows_flushed += len(flows_to_flush)
            
            payload = {"traffic_records": flows_to_flush, "devices": [], "alerts": [], "anomalies": []}
            message_id = str(uuid.uuid4())
            self._db_execute(
                "INSERT INTO outbox_queue (id, payload, status, next_retry) VALUES (?, ?, 'queued', ?)",
                (message_id, json.dumps(payload), time.time())
            )

    def _sender_loop(self):
        """Sends data from SQLite outbox to the Cloud with exponential backoff and compression."""
        headers = {"X-API-Key": AGENT_API_KEY, "Content-Type": "application/json", "Content-Encoding": "gzip"}
        
        while self.is_running:
            time.sleep(3)
            
            # Prepare device sync payload (every cycle)
            with self.lock:
                devices_payload = []
                for mac, d in self.devices.items():
                    devices_payload.append({
                        "mac": d["mac"], "hostname": d["hostname"], "hostname_source": d["hostname_source"],
                        "type": d["type"], "ip": d["ip"], "ip_history": list(d["ip_history"]),
                        "vendor": d["vendor"], "is_randomized_mac": d["is_randomized_mac"], "status": "online"
                    })
            
            if devices_payload:
                msg_id = str(uuid.uuid4())
                self._db_execute(
                    "INSERT INTO outbox_queue (id, payload, status, next_retry) VALUES (?, ?, 'queued', ?)",
                    (msg_id, json.dumps({"devices": devices_payload, "traffic_records": [], "alerts": [], "anomalies": []}), time.time())
                )

            # Disk usage protection
            row = self._db_execute("SELECT count(*) FROM outbox_queue", fetchone=True)
            if row and row[0] > 5000:
                logger.warning("Queue size exceeded 5000. Dropping oldest 500 records.")
                self._db_execute("DELETE FROM outbox_queue WHERE id IN (SELECT id FROM outbox_queue ORDER BY next_retry ASC LIMIT 500)")

            # Fetch up to 5 messages ready to send
            now = time.time()
            rows = self._db_execute(
                "SELECT id, payload, retry_count FROM outbox_queue WHERE status IN ('queued', 'failed') AND next_retry <= ? ORDER BY next_retry ASC LIMIT 5",
                (now,), fetch=True
            )
            
            if not rows:
                continue
                
            for row_id, payload_str, retry_count in rows:
                try:
                    compressed_data = gzip.compress(payload_str.encode('utf-8'))
                    req_headers = headers.copy()
                    req_headers["X-Message-ID"] = row_id
                    
                    # Longer timeout for Render free tier cold starts
                    res = requests.post(CLOUD_API_URL, data=compressed_data, headers=req_headers, timeout=30)
                    
                    if res.status_code in [200, 201, 202]:
                        self._db_execute("DELETE FROM outbox_queue WHERE id = ?", (row_id,))
                        self._messages_sent += 1
                        logger.info(f"[OK] Sent message {row_id[:8]}... to cloud ({res.status_code})")
                    else:
                        new_retry = retry_count + 1
                        jitter = random.uniform(0, 1)
                        backoff = min(now + (2 ** new_retry) + jitter, now + 300)
                        self._db_execute(
                            "UPDATE outbox_queue SET status = 'failed', retry_count = ?, next_retry = ? WHERE id = ?",
                            (new_retry, backoff, row_id)
                        )
                        logger.warning(f"Cloud HTTP {res.status_code} for {row_id[:8]}. Retrying in {int(backoff - now)}s.")
                except requests.exceptions.Timeout:
                    new_retry = retry_count + 1
                    backoff = min(now + (2 ** new_retry) + random.uniform(0, 1), now + 300)
                    self._db_execute(
                        "UPDATE outbox_queue SET status = 'failed', retry_count = ?, next_retry = ? WHERE id = ?",
                        (new_retry, backoff, row_id)
                    )
                    logger.warning(f"Timeout for {row_id[:8]}. Render may be cold-starting. Retry in {int(backoff - now)}s.")
                except Exception as e:
                    new_retry = retry_count + 1
                    backoff = min(now + (2 ** new_retry) + random.uniform(0, 1), now + 300)
                    self._db_execute(
                        "UPDATE outbox_queue SET status = 'failed', retry_count = ?, next_retry = ? WHERE id = ?",
                        (new_retry, backoff, row_id)
                    )
                    logger.warning(f"Connection error for {row_id[:8]}: {e}. Backing off.")

    def _stats_loop(self):
        """Periodically logs capture statistics."""
        while self.is_running:
            time.sleep(15)
            queue_count = 0
            row = self._db_execute("SELECT count(*) FROM outbox_queue", fetchone=True)
            if row: queue_count = row[0]
            logger.info(
                f"[STATS] Packets: {self._packets_captured} | "
                f"Flows flushed: {self._flows_flushed} | "
                f"Msgs sent: {self._messages_sent} | "
                f"Queue: {queue_count} | "
                f"Devices: {len(self.devices)}"
            )

    def _sniff_loop(self):
        logger.info("Agent Capture Engine Started.")
        
        # Windows: explicitly find active interface
        active_iface = None
        try:
            from scapy.all import get_working_ifaces
            for iface in get_working_ifaces():
                if iface.ip and not iface.ip.startswith("127.") and not iface.ip.startswith("169.254"):
                    active_iface = iface
                    break
        except Exception:
            pass

        if active_iface:
            logger.info(f"Using interface: {active_iface.name} ({active_iface.ip})")
        else:
            logger.info("No active interface explicitly found, using Scapy default.")

        while self.is_running:
            try:
                sniff(prn=self._process_packet, store=0, timeout=2, iface=active_iface)
            except Exception as e:
                logger.error(f"Sniffer crashed: {e}")
                time.sleep(2)

sniffer_instance = PacketSniffer()

if __name__ == '__main__':
    import time
    sniffer_instance.start()
    print("Agent is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sniffer_instance.stop()
        print("Agent stopped.")
