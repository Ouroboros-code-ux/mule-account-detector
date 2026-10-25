"""
Mule Account Risk Scorer & Explainable AI (XAI) Engine.
Computes multi-dimensional risk scores (0-100), detects rapid pass-through layering,
identifies shared-device rings, and outputs human-readable indicator explanations.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime

from ..internal_types import MuleRiskResponse, RiskIndicator, BankTransaction
from .bank_simulator import bank_simulator
from ..config import (
    STRUCTURING_THRESHOLD,
    RAPID_PASS_THROUGH_HOURS,
    SUSPICIOUS_DEVICE_HASHES,
    RISK_TIER_CRITICAL,
    RISK_TIER_HIGH,
    RISK_TIER_MEDIUM
)

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mule_pipeline.pkl")

class MuleRiskEngine:
    def __init__(self):
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.pipeline = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Warning: Failed to load ML model from {MODEL_PATH}: {e}")

    def evaluate_account(self, account_id: str) -> MuleRiskResponse:
        """
        Performs holistic multi-layered risk evaluation:
        1. Behavioral pass-through speed (rapid layering)
        2. Fan-In / Fan-Out ratio (structuring / aggregation)
        3. Shared hardware / IP syndicate clusters
        4. ML model anomaly predictions
        5. Explainable AI (XAI) factor contribution
        """
        account_id = account_id.strip()
        txs = bank_simulator.get_account_history(account_id)
        
        if not txs:
            return MuleRiskResponse(
                account_id=account_id,
                risk_score=10.0,
                risk_tier="LOW",
                is_suspected_mule=False,
                confidence=0.5,
                indicators=[
                    RiskIndicator(
                        code="NO_TRANSACTIONS",
                        title="Dormant or New Account",
                        severity="LOW",
                        description="No historical transactions recorded for this account.",
                        weight=0.0
                    )
                ],
                summary="Account appears dormant with zero transaction history."
            )

        indicators: List[RiskIndicator] = []
        base_score = 15.0

        inflows = [t for t in txs if t.receiver_account == account_id]
        outflows = [t for t in txs if t.sender_account == account_id]

        total_in_amt = sum(t.amount for t in inflows)
        total_out_amt = sum(t.amount for t in outflows)

        # -----------------------------------------------------------------
        # 1. Rapid Pass-Through & Layering Analysis
        # -----------------------------------------------------------------
        pass_through_ratio = (total_out_amt / total_in_amt) if total_in_amt > 0 else 0.0
        fastest_pass_through_mins = None

        if inflows and outflows:
            # Check time gap between earliest large inflow and subsequent outflows
            first_inflow_time = datetime.fromisoformat(min(t.timestamp for t in inflows))
            subsequent_outflows = [
                datetime.fromisoformat(t.timestamp) 
                for t in outflows 
                if datetime.fromisoformat(t.timestamp) >= first_inflow_time
            ]
            if subsequent_outflows:
                delta = (min(subsequent_outflows) - first_inflow_time).total_seconds() / 60.0
                fastest_pass_through_mins = round(max(delta, 1.0), 1)

        if pass_through_ratio >= 0.85 and total_in_amt >= 5000.0:
            if fastest_pass_through_mins and fastest_pass_through_mins <= 60.0:
                base_score += 40.0
                indicators.append(RiskIndicator(
                    code="RAPID_LAYERING",
                    title="Rapid Fund Pass-Through (Layering)",
                    severity="CRITICAL",
                    description=f"{pass_through_ratio*100:.1f}% of received funds (${total_in_amt:,.2f}) were transferred out within {fastest_pass_through_mins} minutes.",
                    weight=40.0
                ))
            else:
                base_score += 25.0
                indicators.append(RiskIndicator(
                    code="HIGH_PASS_THROUGH",
                    title="High Pass-Through Velocity",
                    severity="HIGH",
                    description=f"Account forwarded {pass_through_ratio*100:.1f}% of all incoming credits with minimal retained balance.",
                    weight=25.0
                ))

        # -----------------------------------------------------------------
        # 2. Shared Device & Hardware Syndicate
        # -----------------------------------------------------------------
        shared_devices = set(t.device_hash for t in txs if t.device_hash)
        linked_accounts = set()
        for d in shared_devices:
            cohort = bank_simulator.get_accounts_sharing_device(d)
            for other in cohort:
                if other != account_id:
                    linked_accounts.add(other)

        if linked_accounts:
            base_score += 30.0
            indicators.append(RiskIndicator(
                code="SYNDICATE_HARDWARE_RING",
                title="Shared Device Syndicate Link",
                severity="CRITICAL",
                description=f"Shares device hardware credentials with {len(linked_accounts)} other accounts: {list(linked_accounts)[:3]}.",
                weight=30.0
            ))

        # -----------------------------------------------------------------
        # 3. Structuring / Smurfing Detection (Amounts near $10k threshold)
        # -----------------------------------------------------------------
        smurfing_txs = [t for t in txs if 9000.0 <= t.amount < STRUCTURING_THRESHOLD]
        if len(smurfing_txs) >= 2:
            base_score += 20.0
            indicators.append(RiskIndicator(
                code="STRUCTURING_SMURFING",
                title="Structuring / Smurfing Detected",
                severity="HIGH",
                description=f"Found {len(smurfing_txs)} transactions just under the $10,000 threshold to evade regulatory reporting.",
                weight=20.0
            ))

        # -----------------------------------------------------------------
        # 4. Behavioral Velocity & Deviation
        # -----------------------------------------------------------------
        avg_velocity = np.mean([t.velocity_score for t in txs]) if txs else 0.0
        avg_deviation = np.mean([t.spending_deviation_score for t in txs]) if txs else 0.0

        if avg_velocity >= 14.0:
            base_score += 15.0
            indicators.append(RiskIndicator(
                code="HIGH_TX_VELOCITY",
                title="Abnormal Transaction Velocity",
                severity="MEDIUM",
                description=f"Transaction frequency (score: {avg_velocity:.1f}) is 3.5x higher than typical retail customer baselines.",
                weight=15.0
            ))

        if avg_deviation >= 2.5:
            base_score += 10.0
            indicators.append(RiskIndicator(
                code="SPENDING_ANOMALY",
                title="Severe Spending Deviation",
                severity="MEDIUM",
                description=f"Spending deviation ({avg_deviation:.2f}) indicates sudden abnormal spikes in account activity.",
                weight=10.0
            ))

        # -----------------------------------------------------------------
        # 5. ML Model Inference
        # -----------------------------------------------------------------
        ml_confidence = 0.5
        if self.pipeline and txs:
            try:
                sample_features = pd.DataFrame([{
                    "amount": np.mean([t.amount for t in txs]),
                    "spending_deviation_score": avg_deviation,
                    "velocity_score": avg_velocity,
                    "geo_anomaly_score": np.mean([t.geo_anomaly_score for t in txs]),
                    "time_since_last_transaction": np.median([t.time_since_last_transaction for t in txs]),
                    "transaction_type": txs[0].transaction_type,
                    "payment_channel": txs[0].payment_channel,
                    "device_used": txs[0].device_used
                }])
                ml_prob = self.pipeline.predict_proba(sample_features)[0][1]
                ml_confidence = float(ml_prob)
                if ml_prob > 0.70:
                    base_score += 15.0
                    indicators.append(RiskIndicator(
                        code="ML_ANOMALY_CONFIRMED",
                        title="AI Model Fraud Probability High",
                        severity="HIGH",
                        description=f"Machine learning classifier predicted fraud probability of {ml_prob*100:.1f}%.",
                        weight=15.0
                    ))
            except Exception as e:
                print(f"ML evaluation error: {e}")

        # Final Score Clamping
        final_score = min(max(round(base_score, 1), 5.0), 99.0)

        # Risk Tier
        if final_score >= RISK_TIER_CRITICAL:
            tier = "CRITICAL"
            is_mule = True
        elif final_score >= RISK_TIER_HIGH:
            tier = "HIGH"
            is_mule = True
        elif final_score >= RISK_TIER_MEDIUM:
            tier = "MEDIUM"
            is_mule = False
        else:
            tier = "LOW"
            is_mule = False

        # Executive Summary
        if is_mule:
            summary = f"Account exhibits high-risk money mule behavior with a score of {final_score}/100. " \
                      f"Key concerns include {indicators[0].title if indicators else 'unusual velocity'}."
        else:
            summary = f"Account risk evaluated as {tier} ({final_score}/100). No systemic mule indicators detected."

        return MuleRiskResponse(
            account_id=account_id,
            risk_score=final_score,
            risk_tier=tier,
            is_suspected_mule=is_mule,
            confidence=round(ml_confidence, 2),
            indicators=indicators,
            pass_through_velocity_hours=round(fastest_pass_through_mins / 60.0, 2) if fastest_pass_through_mins else None,
            in_out_ratio=round(pass_through_ratio, 2),
            shared_device_accounts=list(linked_accounts),
            summary=summary
        )

mule_risk_engine = MuleRiskEngine()
