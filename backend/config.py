import os
import secrets
import logging
from typing import Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ----------------- Database & Storage -----------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bank_cybercrime.db")
DB_NAME = "bank_cybercrime.db"

# ----------------- AI / LLM Configuration -----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ----------------- Security & JWT -----------------
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours for investigator sessions

# ----------------- SMTP & Verification -----------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8001")

# ----------------- Financial Cybercrime & Mule Thresholds -----------------
STRUCTURING_THRESHOLD = 10000.0  # Common CTR (Currency Transaction Report) threshold
RAPID_PASS_THROUGH_HOURS = 1.0   # If 80%+ of incoming funds are forwarded within 1 hour
HIGH_VELOCITY_TX_COUNT = 15      # >15 tx in a short window
MAX_GRAPH_HOPS = 3               # Depth of money trail network visualization
RISK_TIER_CRITICAL = 80.0
RISK_TIER_HIGH = 65.0
RISK_TIER_MEDIUM = 40.0

# Pre-flagged or Known High-Risk Entities (Sample AML Watchlist)
SUSPICIOUS_DEVICE_HASHES = {
    "D8536477": "Flagged Device: Linked to Telegram Cyber Fraud Syndicate",
    "D2622631": "Flagged Device: High-frequency APK Malware Controller",
    "D9998888": "Flagged Device: Known ATM Casher Relay"
}

SUSPICIOUS_IP_SUBNETS = [
    "185.220.101.",  # Known VPN / Proxy egress node
    "194.26.29."
]