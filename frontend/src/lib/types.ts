// ============================================================
// Personal Data Leak Monitor - Type Definitions
// ============================================================

export interface Device {
  id: string;
  name: string;
  type: 'laptop' | 'phone' | 'tablet' | 'smart-tv' | 'camera' | 'speaker' | 'thermostat' | 'printer' | 'router' | 'unknown';
  ip: string;
  mac: string;
  vendor: string;
  status: 'online' | 'offline' | 'unknown';
  firstSeen: string;
  lastSeen: string;
  totalBytesSent: number;
  totalBytesReceived: number;
  suspiciousConnections: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  icon: string;
}

export interface TrafficRecord {
  id: string;
  timestamp: string;
  sourceIp: string;
  sourceDevice: string;
  destIp: string;
  destDomain: string;
  destCountry: string;
  protocol: 'TCP' | 'UDP' | 'DNS' | 'HTTP' | 'HTTPS' | 'ICMP';
  bytes: number;
  packets: number;
  port: number;
  isSuspicious: boolean;
  riskReason?: string;
}

export interface DNSQuery {
  id: string;
  timestamp: string;
  sourceIp: string;
  sourceDevice: string;
  domain: string;
  queryType: 'A' | 'AAAA' | 'CNAME' | 'MX' | 'TXT' | 'NS' | 'PTR';
  responseIp: string;
  isTracking: boolean;
  isBlocked: boolean;
  category: 'safe' | 'tracking' | 'advertising' | 'malicious' | 'unknown';
  threatScore: number; // 0-100
}

export interface Alert {
  id: string;
  timestamp: string;
  severity: 'info' | 'warning' | 'high' | 'critical';
  type: 'data-leak' | 'unknown-device' | 'suspicious-domain' | 'high-frequency' | 'unusual-traffic' | 'port-scan' | 'anomaly';
  title: string;
  description: string;
  sourceIp: string;
  sourceDevice: string;
  destIp?: string;
  destDomain?: string;
  resolved: boolean;
  actionTaken?: string;
}

export interface AnomalyEvent {
  id: string;
  timestamp: string;
  type: 'traffic_spike' | 'new_device' | 'unusual_destination' | 'data_exfil' | 'pattern_change' | 'dns_tunneling';
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number; // 0-100
  description: string;
  affectedDevice: string;
  details: Record<string, string | number>;
  recommendation: string;
}

export interface NetworkStats {
  totalDevices: number;
  onlineDevices: number;
  totalPackets: number;
  totalBytes: number;
  bytesSent: number;
  bytesReceived: number;
  alertsToday: number;
  unresolvedAlerts: number;
  dnsQueries: number;
  suspiciousDomains: number;
  anomaliesDetected: number;
  captureStatus: 'active' | 'paused' | 'stopped';
  uptime: string;
  avgLatency: number;
}

export interface TimeSeriesPoint {
  time: string;
  bytes: number;
  packets: number;
  mb: number;
  /** @deprecated Use 'mb' instead. Kept for backward compatibility. */
  value?: number;
  label?: string;
}

export interface TrafficByProtocol {
  protocol: string;
  packets: number;
  bytes: number;
  percentage: number;
  color: string;
}

export interface TopDestination {
  domain: string;
  ip: string;
  country: string;
  requests: number;
  bytes: number;
  lastSeen: string;
  category: 'safe' | 'tracking' | 'advertising' | 'malicious' | 'unknown';
}
