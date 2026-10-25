"""
FastAPI Routes for Cybercrime Complaint Registration & Automated Money Trail Correlation.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ..internal_types import CybercrimeComplaint, ComplaintCorrelationResponse
from ..services.complaint_service import complaint_service

router = APIRouter(prefix="/api/complaints", tags=["Cybercrime Complaint Correlation"])

@router.get("/all", response_model=List[CybercrimeComplaint])
def get_all_complaints():
    """
    Returns all registered cybercrime victim complaints.
    """
    return complaint_service.get_all_complaints()

@router.post("/file", response_model=CybercrimeComplaint)
def file_new_complaint(complaint: CybercrimeComplaint):
    """
    Registers a new cybercrime incident / victim report.
    """
    return complaint_service.file_new_complaint(complaint)

@router.get("/correlate/{complaint_id}", response_model=ComplaintCorrelationResponse)
def correlate_complaint_trail(complaint_id: str):
    """
    Correlates a victim complaint with financial transaction trails,
    identifying 1st-hop mules, 2nd-hop layering accounts, and cashout nodes.
    """
    res = complaint_service.correlate_complaint(complaint_id)
    if not res:
        raise HTTPException(status_code=404, detail="Complaint ID not found")
    return res

@router.get("/clusters")
def get_syndicate_clusters():
    """
    Returns groups of multiple victim complaints pointing to the same suspect account or ring.
    """
    return complaint_service.find_syndicate_complaint_clusters()
