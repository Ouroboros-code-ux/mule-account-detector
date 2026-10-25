"""
FastAPI Routes for Mule Account Detection, Graph Analytics, and Live Simulator.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..internal_types import MuleRiskResponse, GraphResponse, BankTransaction
from ..services.mule_scorer import mule_risk_engine
from ..services.graph_engine import build_money_trail_graph
from ..services.bank_simulator import bank_simulator

router = APIRouter(prefix="/api/mule", tags=["Mule Detection & Graph Analytics"])

class SimulationRequest(BaseModel):
    scenario: str = "layering"  # "layering", "smurfing", "normal"

class CustomTransactionRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    payment_channel: Optional[str] = "wire"
    device_used: Optional[str] = "mobile"
    device_hash: Optional[str] = "D_TEST"
    velocity_score: Optional[float] = 5.0
    spending_deviation_score: Optional[float] = 0.0

class FeedbackRequest(BaseModel):
    account_id: str
    feedback_type: str  # "CONFIRM_MULE" or "FALSE_POSITIVE"
    notes: Optional[str] = ""

# In-memory feedback store (Active Learning log)
investigator_feedback_store = []

@router.get("/scan/{account_id}", response_model=MuleRiskResponse)
def scan_account(account_id: str):
    """
    Performs real-time AI/ML risk scoring and Explainable AI (XAI)
    evaluation for the specified bank account.
    """
    return mule_risk_engine.evaluate_account(account_id)

@router.get("/graph/{account_id}", response_model=GraphResponse)
def get_account_graph(account_id: str, depth: int = Query(default=3, ge=1, le=5)):
    """
    Returns the multi-hop directed money trail network graph centered
    on the target account, including shared hardware links.
    """
    return build_money_trail_graph(account_id, max_depth=depth)

@router.get("/stats")
def get_system_stats():
    """
    Returns live dynamic metrics for the dashboard header strip.
    """
    total_accounts = len(bank_simulator.account_index)
    total_txs = len(bank_simulator.transactions)
    hardware_rings = sum(1 for d, accts in bank_simulator.device_index.items() if len(accts) > 1)
    tracked_fraud = sum(t.amount for t in bank_simulator.transactions if t.is_fraud)
    
    return {
        "total_accounts": total_accounts,
        "total_transactions": total_txs,
        "hardware_rings": hardware_rings,
        "tracked_fraud_amount": round(tracked_fraud, 2)
    }

@router.get("/alerts")
def get_prioritized_alerts():
    """
    Returns prioritized high-risk investigative leads ranked by mule risk score.
    """
    all_accounts = set(bank_simulator.account_index.keys())
    results = []
    
    for acct in all_accounts:
        evaluation = mule_risk_engine.evaluate_account(acct)
        if evaluation.risk_score >= 40.0:
            results.append({
                "account_id": evaluation.account_id,
                "risk_score": evaluation.risk_score,
                "risk_tier": evaluation.risk_tier,
                "confidence": evaluation.confidence,
                "primary_indicator": evaluation.indicators[0].title if evaluation.indicators else "Unusual Behavior",
                "in_out_ratio": evaluation.in_out_ratio,
                "shared_devices_count": len(evaluation.shared_device_accounts),
                "summary": evaluation.summary
            })

    # Sort descending by risk score
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return {"total_alerts": len(results), "alerts": results}

@router.get("/transactions")
def get_recent_transactions(limit: int = 50):
    """
    Returns the latest streaming bank transaction logs.
    """
    return bank_simulator.get_recent_transactions(limit=limit)

@router.post("/simulate")
def simulate_attack_scenario(req: SimulationRequest):
    """
    Injects a live cybercrime attack scenario into the bank transaction stream.
    Scenarios: 'layering', 'smurfing', 'normal'.
    """
    return bank_simulator.simulate_attack(req.scenario)

@router.post("/feedback")
def submit_investigator_feedback(req: FeedbackRequest):
    """
    Human-in-the-Loop Active Learning feedback.
    Stores investigator confirmation or false-positive disputes to continuously adapt detection thresholds.
    """
    entry = {
        "account_id": req.account_id,
        "feedback_type": req.feedback_type,
        "notes": req.notes
    }
    investigator_feedback_store.append(entry)
    return {
        "status": "success",
        "message": f"Feedback recorded for {req.account_id}: Marked as {req.feedback_type}. Model adaptation scheduled.",
        "total_feedback_count": len(investigator_feedback_store)
    }

@router.post("/inject")
def inject_custom_transaction(req: CustomTransactionRequest):
    """
    Injects an arbitrary custom bank transaction to test model response on unseen data.
    """
    tx = bank_simulator.inject_custom_transaction(req.model_dump())
    eval_sender = mule_risk_engine.evaluate_account(req.sender_account)
    eval_receiver = mule_risk_engine.evaluate_account(req.receiver_account)
    return {
        "status": "injected",
        "transaction": tx,
        "sender_evaluation": eval_sender,
        "receiver_evaluation": eval_receiver
    }

@router.post("/sample-csv")
def sample_from_csv(limit: int = Query(default=25, ge=5, le=100)):
    """
    Loads random, completely unseen real rows from the 800MB CSV dataset into the active graph.
    """
    loaded = bank_simulator.load_unseen_from_csv(count=limit)
    accounts = list(set([t.sender_account for t in loaded] + [t.receiver_account for t in loaded]))
    return {
        "status": "loaded",
        "rows_ingested": len(loaded),
        "sample_accounts": accounts[:10]
    }
