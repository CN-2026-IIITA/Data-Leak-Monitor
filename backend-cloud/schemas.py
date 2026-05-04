from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    is_active: bool
    role: str

    class Config:
        from_attributes = True

class APIKeyBase(BaseModel):
    name: str

class APIKeyCreate(APIKeyBase):
    pass

class APIKey(APIKeyBase):
    id: str
    key: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Devices ---
class DeviceBase(BaseModel):
    mac: str
    hostname: Optional[str] = None
    hostname_source: str = "unknown"
    type: str = "unknown"
    ip: str
    ip_history: List[str] = []
    vendor: Optional[str] = None
    is_randomized_mac: bool = False
    status: str = "offline"

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    first_seen: datetime
    last_seen: Optional[datetime]

    class Config:
        from_attributes = True

# --- Traffic Records ---
class TrafficRecordBase(BaseModel):
    timestamp_start: datetime
    timestamp_end: Optional[datetime] = None
    src_ip: str
    dest_ip: str
    src_mac: Optional[str] = None
    dest_mac: Optional[str] = None
    device_mac: Optional[str] = None
    direction: str
    protocol: str
    src_port: Optional[int] = None
    dest_port: Optional[int] = None
    bytes: int
    packets: int
    tcp_flags_seen: int = 0
    min_ttl: Optional[int] = None
    domain: Optional[str] = None
    domain_source: str = "unknown"
    dest_country: Optional[str] = None
    is_suspicious: bool = False
    risk_reason: Optional[str] = None

class TrafficRecordCreate(TrafficRecordBase):
    id: str

class TrafficRecord(TrafficRecordBase):
    id: str

    class Config:
        from_attributes = True

# --- Device Baselines ---
class DeviceBaselineBase(BaseModel):
    device_mac: str
    time_window: str
    avg_bytes_per_hour: int = 0
    top_ports: List[Any] = []
    top_domains: List[Any] = []

class DeviceBaselineCreate(DeviceBaselineBase):
    id: str

class DeviceBaseline(DeviceBaselineBase):
    id: str
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Alerts ---
class AlertBase(BaseModel):
    alert_key: Optional[str] = None
    occurrence_count: int = 1
    status: str = "pending"
    severity: str
    type: str
    title: str
    description: str
    device_mac: Optional[str] = None
    dest_ip: Optional[str] = None
    dest_domain: Optional[str] = None
    resolved: bool = False
    action_taken: Optional[str] = None

class AlertCreate(AlertBase):
    id: str

class Alert(AlertBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Anomalies ---
class AnomalyBase(BaseModel):
    type: str
    severity: str
    confidence: int
    description: str
    device_mac: Optional[str] = None
    details: Dict[str, Any]
    recommendation: str

class AnomalyCreate(AnomalyBase):
    id: str

class Anomaly(AnomalyBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Agent Ingest (Batch) ---
class AgentPayload(BaseModel):
    devices: List[DeviceCreate] = []
    traffic_records: List[TrafficRecordCreate] = []
    alerts: List[AlertCreate] = []
    anomalies: List[AnomalyCreate] = []

# --- Setup Wizard ---
class SetupInitialize(BaseModel):
    email: str
    password: str
    company_name: Optional[str] = "Personal"