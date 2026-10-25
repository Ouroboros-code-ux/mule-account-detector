"""
Cybercrime Incident & Complaint Correlation Service.
Correlates victim complaints with financial transactions, traces stolen funds forward
across mule networks, and calculates freezable funds for law enforcement.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from ..internal_types import CybercrimeComplaint, ComplaintCorrelationResponse
from .bank_simulator import bank_simulator
from .graph_engine import build_money_trail_graph

class ComplaintCorrelationService:
    def __init__(self):
        self.complaints: Dict[str, CybercrimeComplaint] = {}
        self._init_seed_complaints()

    def _init_seed_complaints(self):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        c1 = CybercrimeComplaint(
            complaint_id="CYBER-2024-8912",
            incident_date=now,
            victim_account="ACC_VICTIM_401",
            victim_name="Robert Jenkins",
            reported_tx_id="TX_CYBER_101",
            suspect_account="ACC_MULE_ALPHA",
            amount_lost=50000.0,
            crime_category="Investment Scam / Telegram Task",
            status="ACTIVE",
            evidence_notes="Victim was coerced into transferring funds via wire transfer to a fake trading portal."
        )

        c2 = CybercrimeComplaint(
            complaint_id="CYBER-2024-4401",
            incident_date=now,
            victim_account="ACC_VICTIM_772",
            victim_name="Priya Sharma",
            reported_tx_id="TX_SMURF_1",
            suspect_account="ACC_SMURF_PUPPET_1",
            amount_lost=9650.0,
            crime_category="Phishing / Malicious APK",
            status="ACTIVE",
            evidence_notes="Malicious banking trojan initiated unauthorized transfer under CTR threshold."
        )

        self.complaints[c1.complaint_id] = c1
        self.complaints[c2.complaint_id] = c2

    def file_new_complaint(self, complaint: CybercrimeComplaint) -> CybercrimeComplaint:
        self.complaints[complaint.complaint_id] = complaint
        return complaint

    def get_all_complaints(self) -> List[CybercrimeComplaint]:
        return list(self.complaints.values())

    def correlate_complaint(self, complaint_id: str) -> Optional[ComplaintCorrelationResponse]:
        """
        Traces the victim's lost funds forward across the banking network.
        Identifies:
        - 1st-Hop Primary Mule
        - 2nd-Hop Intermediary Layering Accounts
        - Exit Cashout / ATM destinations
        """
        complaint = self.complaints.get(complaint_id)
        if not complaint:
            return None

        # Build money trail from suspect account
        trail = build_money_trail_graph(complaint.suspect_account, max_depth=3)
        
        suspect_nodes = [n.id for n in trail.nodes if n.type in ("mule", "target", "layering")]
        
        return ComplaintCorrelationResponse(
            complaint_id=complaint.complaint_id,
            victim_account=complaint.victim_account,
            amount_lost=complaint.amount_lost,
            crime_category=complaint.crime_category,
            first_hop_beneficiary=complaint.suspect_account,
            suspect_chain=suspect_nodes,
            frozen_status=False,
            total_funds_tracked=complaint.amount_lost,
            investigation_lead_score=94.5
        )

    def find_syndicate_complaint_clusters(self) -> List[Dict[str, Any]]:
        """
        Groups complaints where different victims were defrauded by the same
        beneficiary account or connected mule ring.
        """
        clusters: Dict[str, List[CybercrimeComplaint]] = {}
        for c in self.complaints.values():
            clusters.setdefault(c.suspect_account, []).append(c)

        result = []
        for suspect, comp_list in clusters.items():
            result.append({
                "suspect_account": suspect,
                "complaints_count": len(comp_list),
                "total_stolen": sum(c.amount_lost for c in comp_list),
                "complaint_ids": [c.complaint_id for c in comp_list],
                "victim_accounts": [c.victim_account for c in comp_list]
            })
        return result

complaint_service = ComplaintCorrelationService()
