"""
Realistic Bank Transaction Stream & Cybercrime Attack Simulator.
Provides live banking logs, multi-hop layering scenarios, smurfing attacks,
and shared-device mule rings for detection, graph tracing, and testing.
"""

import os
import random
import uuid
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple, Any

from ..internal_types import BankTransaction

CSV_DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "financial_fraud_detection_dataset.csv")

class BankLogSimulator:
    def __init__(self):
        self.transactions: List[BankTransaction] = []
        self.account_index: Dict[str, List[BankTransaction]] = {}
        self.device_index: Dict[str, set] = {}
        self._init_seed_scenarios()

    def inject_custom_transaction(self, data: Dict[str, Any]) -> BankTransaction:
        """Injects an arbitrary, user-defined bank transaction to test model generalization."""
        now = datetime.now(timezone.utc).isoformat()
        tx = BankTransaction(
            transaction_id=data.get("transaction_id", f"TX_CUST_{uuid.uuid4().hex[:6].upper()}"),
            timestamp=data.get("timestamp", now),
            sender_account=data.get("sender_account", "ACC_TEST_SENDER").strip(),
            receiver_account=data.get("receiver_account", "ACC_TEST_RECEIVER").strip(),
            amount=float(data.get("amount", 1000.0)),
            transaction_type=data.get("transaction_type", "transfer"),
            payment_channel=data.get("payment_channel", "wire"),
            device_used=data.get("device_used", "mobile"),
            device_hash=data.get("device_hash", f"D_CUSTOM_{uuid.uuid4().hex[:4].upper()}"),
            ip_address=data.get("ip_address", "192.168.1.100"),
            location=data.get("location", "Unknown"),
            velocity_score=float(data.get("velocity_score", 5.0)),
            spending_deviation_score=float(data.get("spending_deviation_score", 0.0)),
            geo_anomaly_score=float(data.get("geo_anomaly_score", 0.1)),
            time_since_last_transaction=float(data.get("time_since_last_transaction", 60.0)),
            is_fraud=False,
            fraud_type=None
        )
        self.add_transaction(tx)
        return tx

    def load_unseen_from_csv(self, count: int = 50) -> List[BankTransaction]:
        """Reads completely random, unseen rows directly from the 800MB CSV dataset."""
        if not os.path.exists(CSV_DATASET_PATH):
            return []

        # Read a random chunk from the CSV
        skip_rows = random.randint(100, 2000000)
        df_chunk = pd.read_csv(CSV_DATASET_PATH, skiprows=range(1, skip_rows), nrows=count)
        
        loaded = []
        for _, row in df_chunk.iterrows():
            try:
                tx = BankTransaction(
                    transaction_id=str(row.get("transaction_id", uuid.uuid4().hex[:6])),
                    timestamp=str(row.get("timestamp", datetime.now(timezone.utc).isoformat())),
                    sender_account=str(row.get("sender_account", "ACC_UNKNOWN")),
                    receiver_account=str(row.get("receiver_account", "ACC_UNKNOWN")),
                    amount=float(row.get("amount", 100.0)),
                    transaction_type=str(row.get("transaction_type", "transfer")),
                    payment_channel=str(row.get("payment_channel", "card")),
                    device_used=str(row.get("device_used", "mobile")),
                    device_hash=str(row.get("device_hash", "D_UNSEEN")),
                    ip_address=str(row.get("ip_address", "0.0.0.0")),
                    location=str(row.get("location", "Global")),
                    velocity_score=float(row.get("velocity_score", 5.0)) if pd.notnull(row.get("velocity_score")) else 5.0,
                    spending_deviation_score=float(row.get("spending_deviation_score", 0.0)) if pd.notnull(row.get("spending_deviation_score")) else 0.0,
                    geo_anomaly_score=float(row.get("geo_anomaly_score", 0.1)) if pd.notnull(row.get("geo_anomaly_score")) else 0.1,
                    time_since_last_transaction=float(row.get("time_since_last_transaction", 60.0)) if pd.notnull(row.get("time_since_last_transaction")) else 60.0,
                    is_fraud=bool(row.get("is_fraud", False)),
                    fraud_type=str(row.get("fraud_type")) if pd.notnull(row.get("fraud_type")) else None
                )
                self.add_transaction(tx)
                loaded.append(tx)
            except Exception as e:
                continue
        return loaded

    def add_transaction(self, tx: BankTransaction):
        self.transactions.append(tx)
        
        # Index by sender
        if tx.sender_account not in self.account_index:
            self.account_index[tx.sender_account] = []
        self.account_index[tx.sender_account].append(tx)

        # Index by receiver
        if tx.receiver_account not in self.account_index:
            self.account_index[tx.receiver_account] = []
        self.account_index[tx.receiver_account].append(tx)

        # Index by device hash
        if tx.device_hash not in self.device_index:
            self.device_index[tx.device_hash] = set()
        self.device_index[tx.device_hash].add(tx.sender_account)
        self.device_index[tx.device_hash].add(tx.receiver_account)

    def get_account_history(self, account_id: str) -> List[BankTransaction]:
        return self.account_index.get(account_id, [])

    def get_recent_transactions(self, limit: int = 50) -> List[BankTransaction]:
        return sorted(self.transactions, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_accounts_sharing_device(self, device_hash: str) -> List[str]:
        return list(self.device_index.get(device_hash, set()))

    def _init_seed_scenarios(self):
        """Pre-populates realistic cybercrime fraud networks and normal banking baseline."""
        now = datetime.now(timezone.utc)

        # ==============================================================================
        # SCENARIO 1: Rapid Multi-Hop Layering Chain (Victim -> Mule 1 -> Mules 2,3,4 -> Cashout)
        # ==============================================================================
        victim_acct = "ACC_VICTIM_401"
        mule_1 = "ACC_MULE_ALPHA"
        mule_2 = "ACC_MULE_BETA"
        mule_3 = "ACC_MULE_GAMMA"
        mule_4 = "ACC_MULE_DELTA"

        # Hop 0: Victim transfers $50,000 (Cybercrime Fraud loss)
        t0 = (now - timedelta(hours=3)).isoformat()
        self.add_transaction(BankTransaction(
            transaction_id="TX_CYBER_101",
            timestamp=t0,
            sender_account=victim_acct,
            receiver_account=mule_1,
            amount=50000.0,
            transaction_type="transfer",
            payment_channel="wire",
            device_used="web",
            device_hash="D_VICTIM_01",
            ip_address="102.16.88.12",
            location="Chicago",
            velocity_score=1.0,
            spending_deviation_score=2.8,
            geo_anomaly_score=0.1,
            is_fraud=True,
            fraud_type="cybercrime_victim_transfer"
        ))

        # Hop 1: Rapid Dispersal within 6 minutes (98% of funds forwarded)
        t1 = (now - timedelta(hours=2, minutes=54)).isoformat()
        for idx, (target, amt) in enumerate([(mule_2, 16500.0), (mule_3, 16500.0), (mule_4, 16000.0)]):
            self.add_transaction(BankTransaction(
                transaction_id=f"TX_LAYER_H1_{idx+1}",
                timestamp=t1,
                sender_account=mule_1,
                receiver_account=target,
                amount=amt,
                transaction_type="transfer",
                payment_channel="wire",
                device_used="mobile",
                device_hash="D8536477",
                ip_address="185.220.101.44",
                location="Miami",
                velocity_score=18.0,
                spending_deviation_score=4.5,
                geo_anomaly_score=0.92,
                time_since_last_transaction=6.0,
                is_fraud=True,
                fraud_type="mule_layering"
            ))

        # Hop 2: Cashout at ATM / Crypto Exchange within 15 minutes
        t2 = (now - timedelta(hours=2, minutes=40)).isoformat()
        for idx, source in enumerate([mule_2, mule_3, mule_4]):
            self.add_transaction(BankTransaction(
                transaction_id=f"TX_CASHOUT_{idx+1}",
                timestamp=t2,
                sender_account=source,
                receiver_account="ATM_CASHOUT_GATEWAY",
                amount=15800.0,
                transaction_type="withdrawal",
                payment_channel="card",
                device_used="atm",
                device_hash="D8536477",
                ip_address="185.220.101.44",
                location="Miami",
                velocity_score=19.0,
                spending_deviation_score=3.9,
                geo_anomaly_score=0.95,
                time_since_last_transaction=14.0,
                is_fraud=True,
                fraud_type="mule_cashout"
            ))

        # ==============================================================================
        # SCENARIO 2: Smurfing / Structuring Attack (Split amounts under $10,000)
        # ==============================================================================
        smurf_aggregator = "ACC_SMURF_BOSS"
        for i in range(5):
            t_smurf = (now - timedelta(hours=4, minutes=i*20)).isoformat()
            self.add_transaction(BankTransaction(
                transaction_id=f"TX_SMURF_{i+1}",
                timestamp=t_smurf,
                sender_account=f"ACC_SMURF_PUPPET_{i+1}",
                receiver_account=smurf_aggregator,
                amount=round(random.uniform(9200.0, 9850.0), 2),
                transaction_type="transfer",
                payment_channel="ACH",
                device_used="mobile",
                device_hash="D2622631",
                ip_address="172.52.47.194",
                location="Dallas",
                velocity_score=16.0,
                spending_deviation_score=2.9,
                geo_anomaly_score=0.88,
                time_since_last_transaction=20.0,
                is_fraud=True,
                fraud_type="structuring_smurfing"
            ))

        # ==============================================================================
        # SCENARIO 3: Shared Device Mule Syndicate (5 accounts operating from 1 phone)
        # ==============================================================================
        ring_accounts = [f"ACC_SYNDICATE_{i+1}" for i in range(4)]
        shared_device = "D9998888"
        for i in range(len(ring_accounts)):
            next_acct = ring_accounts[(i + 1) % len(ring_accounts)]
            t_ring = (now - timedelta(hours=5, minutes=i*15)).isoformat()
            self.add_transaction(BankTransaction(
                transaction_id=f"TX_RING_{i+1}",
                timestamp=t_ring,
                sender_account=ring_accounts[i],
                receiver_account=next_acct,
                amount=8500.0 + (i * 250),
                transaction_type="transfer",
                payment_channel="UPI",
                device_used="mobile",
                device_hash=shared_device,
                ip_address="194.26.29.80",
                location="Los Angeles",
                velocity_score=15.0,
                spending_deviation_score=3.2,
                geo_anomaly_score=0.85,
                time_since_last_transaction=15.0,
                is_fraud=True,
                fraud_type="mule_syndicate_ring"
            ))

        # ==============================================================================
        # SCENARIO 4: Legitimate Everyday Banking Baseline
        # ==============================================================================
        legit_accounts = ["ACC_CORP_PAYROLL", "ACC_ALICE_RETAIL", "ACC_BOB_SALARY", "ACC_CITY_POWER", "ACC_COFFEE_SHOP"]
        for i in range(25):
            src = random.choice(legit_accounts)
            dst = random.choice([a for a in legit_accounts if a != src])
            t_legit = (now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))).isoformat()
            self.add_transaction(BankTransaction(
                transaction_id=f"TX_NORM_{1000 + i}",
                timestamp=t_legit,
                sender_account=src,
                receiver_account=dst,
                amount=round(random.uniform(15.0, 750.0), 2),
                transaction_type=random.choice(["payment", "transfer", "withdrawal", "deposit"]),
                payment_channel=random.choice(["card", "ACH", "wire"]),
                device_used=random.choice(["mobile", "pos", "web"]),
                device_hash=f"D_LEGIT_{random.randint(100, 999)}",
                ip_address=f"24.112.{random.randint(10, 200)}.{random.randint(10, 250)}",
                location=random.choice(["New York", "Boston", "Seattle"]),
                velocity_score=random.uniform(1.0, 5.0),
                spending_deviation_score=random.uniform(-0.5, 0.8),
                geo_anomaly_score=random.uniform(0.05, 0.35),
                time_since_last_transaction=random.uniform(120.0, 2880.0),
                is_fraud=False,
                fraud_type=None
            ))

    def simulate_attack(self, scenario_name: str) -> Dict[str, Any]:
        """Generates dynamic live attack patterns when requested by the dashboard."""
        now = datetime.now(timezone.utc)
        generated_txs = []

        if scenario_name == "layering":
            lead_victim = f"ACC_VICTIM_{random.randint(500, 999)}"
            prime_mule = f"ACC_MULE_NEW_{random.randint(100, 999)}"
            mules = [f"ACC_HOP_{i}_{random.randint(10, 99)}" for i in range(3)]
            
            # Step 1: Phishing theft
            t0 = now.isoformat()
            tx0 = BankTransaction(
                transaction_id=f"TX_SIM_{uuid.uuid4().hex[:6].upper()}",
                timestamp=t0,
                sender_account=lead_victim,
                receiver_account=prime_mule,
                amount=60000.0,
                transaction_type="transfer",
                payment_channel="wire",
                device_used="web",
                device_hash="D_VICTIM_WEB",
                ip_address="66.249.65.1",
                location="Atlanta",
                velocity_score=2.0,
                spending_deviation_score=4.0,
                geo_anomaly_score=0.1,
                is_fraud=True,
                fraud_type="phishing_victim"
            )
            self.add_transaction(tx0)
            generated_txs.append(tx0)

            # Step 2: Layering pass-through
            t1 = (now + timedelta(minutes=4)).isoformat()
            for m in mules:
                tx_hop = BankTransaction(
                    transaction_id=f"TX_SIM_{uuid.uuid4().hex[:6].upper()}",
                    timestamp=t1,
                    sender_account=prime_mule,
                    receiver_account=m,
                    amount=19500.0,
                    transaction_type="transfer",
                    payment_channel="wire",
                    device_used="mobile",
                    device_hash="D8536477",
                    ip_address="185.220.101.44",
                    location="Miami",
                    velocity_score=22.0,
                    spending_deviation_score=4.8,
                    geo_anomaly_score=0.96,
                    time_since_last_transaction=4.0,
                    is_fraud=True,
                    fraud_type="mule_layering"
                )
                self.add_transaction(tx_hop)
                generated_txs.append(tx_hop)

            return {
                "scenario": "Rapid Multi-Hop Layering Attack",
                "target_account": prime_mule,
                "victim_account": lead_victim,
                "amount": 60000.0,
                "transactions_generated": len(generated_txs)
            }

        elif scenario_name == "smurfing":
            aggregator = f"ACC_SMURF_KING_{random.randint(100, 999)}"
            for i in range(4):
                t = (now - timedelta(minutes=i*10)).isoformat()
                tx = BankTransaction(
                    transaction_id=f"TX_SIM_{uuid.uuid4().hex[:6].upper()}",
                    timestamp=t,
                    sender_account=f"ACC_PUPPET_{random.randint(100, 999)}",
                    receiver_account=aggregator,
                    amount=9500.0 + random.randint(10, 400),
                    transaction_type="transfer",
                    payment_channel="ACH",
                    device_used="mobile",
                    device_hash="D2622631",
                    ip_address="172.52.47.194",
                    location="Dallas",
                    velocity_score=17.0,
                    spending_deviation_score=3.1,
                    geo_anomaly_score=0.89,
                    time_since_last_transaction=10.0,
                    is_fraud=True,
                    fraud_type="structuring_smurfing"
                )
                self.add_transaction(tx)
                generated_txs.append(tx)

            return {
                "scenario": "Smurfing / Structuring Inflow",
                "target_account": aggregator,
                "transactions_generated": len(generated_txs)
            }

        else:
            # Generate normal transactions
            for _ in range(5):
                src = f"ACC_USER_{random.randint(100, 150)}"
                dst = f"ACC_USER_{random.randint(151, 200)}"
                tx = BankTransaction(
                    transaction_id=f"TX_NORM_{uuid.uuid4().hex[:6].upper()}",
                    timestamp=now.isoformat(),
                    sender_account=src,
                    receiver_account=dst,
                    amount=round(random.uniform(25.0, 350.0), 2),
                    transaction_type="payment",
                    payment_channel="card",
                    device_used="pos",
                    device_hash=f"D_POS_{random.randint(100, 999)}",
                    ip_address="12.34.56.78",
                    location="Denver",
                    velocity_score=2.0,
                    spending_deviation_score=0.1,
                    geo_anomaly_score=0.1,
                    time_since_last_transaction=360.0,
                    is_fraud=False,
                    fraud_type=None
                )
                self.add_transaction(tx)
                generated_txs.append(tx)

            return {
                "scenario": "Normal Legitimate Stream",
                "transactions_generated": len(generated_txs)
            }

# Global singleton instance
bank_simulator = BankLogSimulator()
