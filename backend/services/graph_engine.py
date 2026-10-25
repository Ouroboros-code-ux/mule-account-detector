"""
Graph Analytics Engine for Mule Account & Money Trail Investigations.
Builds directed multi-hop transaction networks, detects layering pass-through,
identifies shared-device syndicate rings, and computes flow metrics.
"""

import networkx as nx
from typing import Dict, List, Set, Tuple

from ..internal_types import GraphResponse, GraphNode, GraphEdge
from .bank_simulator import bank_simulator
from ..config import SUSPICIOUS_DEVICE_HASHES, MAX_GRAPH_HOPS

def build_money_trail_graph(target_account: str, max_depth: int = MAX_GRAPH_HOPS) -> GraphResponse:
    """
    Constructs an interactive multi-hop money trail graph centered on target_account.
    Traces incoming victim funds, layering intermediary hops, and exit cashout points.
    """
    target_account = target_account.strip()
    G = nx.DiGraph()

    nodes_dict: Dict[str, GraphNode] = {}
    edges_list: List[GraphEdge] = []
    
    visited_accounts: Set[str] = set()
    queue: List[Tuple[str, int]] = [(target_account, 0)]
    
    total_inflow = 0.0
    total_outflow = 0.0

    while queue:
        current_acct, depth = queue.pop(0)
        if current_acct in visited_accounts or depth > max_depth:
            continue
        visited_accounts.add(current_acct)

        txs = bank_simulator.get_account_history(current_acct)
        for tx in txs:
            src = tx.sender_account
            dst = tx.receiver_account
            amt = tx.amount

            # Track flows for target
            if current_acct == target_account:
                if dst == target_account:
                    total_inflow += amt
                elif src == target_account:
                    total_outflow += amt

            # Add to NetworkX directed graph
            if G.has_edge(src, dst):
                G[src][dst]["amount"] += amt
                G[src][dst]["count"] += 1
            else:
                G.add_edge(src, dst, amount=amt, count=1, timestamp=tx.timestamp)

            # Enqueue next hops
            neighbor = dst if src == current_acct else src
            if neighbor not in visited_accounts and depth < max_depth:
                queue.append((neighbor, depth + 1))

    # Calculate pass-through ratio
    pass_through_ratio = 0.0
    if total_inflow > 0:
        pass_through_ratio = min(total_outflow / total_inflow, 1.0)

    # Detect shared devices across neighborhood
    device_to_accounts: Dict[str, List[str]] = {}
    for acct in visited_accounts:
        acct_txs = bank_simulator.get_account_history(acct)
        for t in acct_txs:
            if t.device_hash:
                device_to_accounts.setdefault(t.device_hash, []).append(acct)

    mule_ring_detected = False
    shared_device_edges = []
    for d_hash, acct_list in device_to_accounts.items():
        unique_accts = list(set(acct_list))
        if len(unique_accts) > 1 and d_hash in SUSPICIOUS_DEVICE_HASHES:
            mule_ring_detected = True
            for i in range(len(unique_accts)):
                for j in range(i + 1, len(unique_accts)):
                    shared_device_edges.append(GraphEdge(
                        source=unique_accts[i],
                        target=unique_accts[j],
                        amount=0.0,
                        transaction_count=1,
                        edge_type="shared_device"
                    ))

    # Build node models without emojis
    for node_id in G.nodes():
        in_deg = G.in_degree(node_id)
        out_deg = G.out_degree(node_id)
        vol = sum([d.get("amount", 0.0) for _, _, d in G.in_edges(node_id, data=True)]) + \
              sum([d.get("amount", 0.0) for _, _, d in G.out_edges(node_id, data=True)])

        # Determine node type and clean label
        if node_id == target_account:
            n_type = "target"
            label = f"Target: {node_id}"
            score = 85.0 if pass_through_ratio > 0.8 else 50.0
        elif "ATM" in node_id or "CASHOUT" in node_id:
            n_type = "cashout"
            label = f"Cashout: {node_id}"
            score = 90.0
        elif "VICTIM" in node_id:
            n_type = "victim"
            label = f"Victim: {node_id}"
            score = 10.0
        elif in_deg > 0 and out_deg > 0:
            n_type = "mule"
            label = f"Mule: {node_id}"
            score = 80.0
        else:
            n_type = "normal"
            label = node_id
            score = 25.0

        nodes_dict[node_id] = GraphNode(
            id=node_id,
            label=label,
            type=n_type,
            risk_score=score,
            total_volume=round(vol, 2),
            in_degree=in_deg,
            out_degree=out_deg
        )

    # Build directed transaction edges
    for u, v, data in G.edges(data=True):
        edges_list.append(GraphEdge(
            source=u,
            target=v,
            amount=round(data["amount"], 2),
            transaction_count=data["count"],
            edge_type="funds_flow",
            latest_timestamp=data.get("timestamp")
        ))

    edges_list.extend(shared_device_edges)

    return GraphResponse(
        target_account=target_account,
        nodes=list(nodes_dict.values()),
        edges=edges_list,
        total_inflow=round(total_inflow, 2),
        total_outflow=round(total_outflow, 2),
        pass_through_ratio=round(pass_through_ratio, 2),
        mule_ring_detected=mule_ring_detected
    )
