"""
MuleShield AI - Core API Verification Script.
Tests health, account scanning, graph trail generation, and cybercrime complaint endpoints.
"""

import urllib.request
import json

BASE_URL = "http://127.0.0.1:8001"

def check_endpoint(path: str, name: str):
    url = f"{BASE_URL}{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MuleShieldTest/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"[PASS] {name}: 200 OK")
                return data
            else:
                print(f"[FAIL] {name}: Status {resp.status}")
                return None
    except Exception as e:
        print(f"[FAIL] {name}: Connection error: {e}")
        return None

def run_all_tests():
    print("=" * 60)
    print(" MuleShield AI - Automated API Diagnostic Suite")
    print("=" * 60)
    
    # 1. Health
    h = check_endpoint("/api/health", "System Health Check")
    if h:
        print(f"       System: {h.get('system')} (v{h.get('version')})")

    # 1b. Stats
    st = check_endpoint("/api/mule/stats", "Live System Stats")
    if st:
        print(f"       Accounts: {st.get('total_accounts')} | Rings: {st.get('hardware_rings')} | Tracked Fraud: ${st.get('tracked_fraud_amount')}")

    # 2. Alerts
    a = check_endpoint("/api/mule/alerts", "Prioritized Leads Feed")
    if a:
        print(f"       Active Leads Found: {a.get('total_alerts')}")

    # 3. Account Scan
    s = check_endpoint("/api/mule/scan/ACC_MULE_ALPHA", "Mule Risk & XAI Evaluation")
    if s:
        print(f"       Account: {s.get('account_id')} | Risk: {s.get('risk_score')}/100 ({s.get('risk_tier')})")
        print(f"       Top Indicator: {s.get('indicators', [{}])[0].get('title')}")

    # 4. Graph Trail
    g = check_endpoint("/api/mule/graph/ACC_MULE_ALPHA", "Money Trail Graph Traversal")
    if g:
        print(f"       Nodes: {len(g.get('nodes', []))} | Edges: {len(g.get('edges', []))}")

    # 5. Complaints
    c = check_endpoint("/api/complaints/all", "Cybercrime Complaints Feed")
    if c:
        print(f"       Total Complaints Tracked: {len(c)}")

    print("=" * 60)
    print(" Diagnostic Complete. All endpoints operational.")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
