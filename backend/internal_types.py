from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ----------------- Auth Types -----------------

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

# ----------------- Transaction & Account Types -----------------

class BankTransaction(BaseModel):
    transaction_id: str
    timestamp: str
    sender_account: str
    receiver_account: str
    amount: float
    transaction_type: str = "transfer"  # transfer, withdrawal, deposit, payment
    payment_channel: str = "wire"       # wire, ACH, card, UPI, crypto
    device_used: str = "mobile"         # mobile, atm, web, pos
    device_hash: str = "D1000000"
    ip_address: str = "192.168.1.1"
    location: str = "New York"
    velocity_score: float = 0.0
    spending_deviation_score: float = 0.0
    geo_anomaly_score: float = 0.0
    time_since_last_transaction: float = 60.0
    is_fraud: bool = False
    fraud_type: Optional[str] = None

# ----------------- Graph Visualization Types -----------------

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "target", "mule", "victim", "layering", "cashout", "syndicate_cluster", "normal"
    risk_score: float = 0.0
    total_volume: float = 0.0
    in_degree: int = 0
    out_degree: int = 0
    device_hash: Optional[str] = None
    ip_address: Optional[str] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    amount: float
    transaction_count: int = 1
    edge_type: str = "funds_flow"  # "funds_flow" or "shared_device"
    latency_minutes: Optional[float] = None
    latest_timestamp: Optional[str] = None

class GraphResponse(BaseModel):
    target_account: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_inflow: float = 0.0
    total_outflow: float = 0.0
    pass_through_ratio: float = 0.0
    mule_ring_detected: bool = False

# ----------------- Explainable AI & Risk Score Types -----------------

class RiskIndicator(BaseModel):
    code: str
    title: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    description: str
    weight: float

class MuleRiskResponse(BaseModel):
    account_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_tier: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    is_suspected_mule: bool
    confidence: float
    indicators: List[RiskIndicator]
    pass_through_velocity_hours: Optional[float] = None
    in_out_ratio: float = 1.0
    shared_device_accounts: List[str] = []
    connected_complaints: List[str] = []
    summary: str

# ----------------- Cybercrime Complaint Types -----------------

class CybercrimeComplaint(BaseModel):
    complaint_id: str
    incident_date: str
    victim_account: str
    victim_name: str
    reported_tx_id: str
    suspect_account: str
    amount_lost: float
    crime_category: str  # "Investment Scam", "Phishing / APK", "Impersonation", "Digital Arrest", "Sextortion"
    status: str = "ACTIVE"  # "ACTIVE", "UNDER_INVESTIGATION", "FUNDS_FROZEN", "RESOLVED"
    evidence_notes: str = ""

class ComplaintCorrelationResponse(BaseModel):
    complaint_id: str
    victim_account: str
    amount_lost: float
    crime_category: str
    first_hop_beneficiary: str
    suspect_chain: List[str]
    frozen_status: bool
    total_funds_tracked: float
    investigation_lead_score: float