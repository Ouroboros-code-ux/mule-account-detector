# MuleShield.AI: Autonomous Mule Account & Cybercrime Network Detection Engine

MuleShield.AI is an advanced AI/ML and Graph Analytics solution designed for financial institutions, intelligence units, and law-enforcement agencies to detect suspected money mule accounts, trace illicit fund layering across multi-hop trails, correlate cybercrime complaints, and dismantle organized fraud syndicates.

---

## Problem Statement & Solution Matrix

| Requirement | Implementation in MuleShield.AI |
| :--- | :--- |
| **Transaction Analysis** | Real-time velocity scoring, rapid fund transfer tracking, spending deviation, and pass-through flow analysis. Detects structuring (smurfing) under regulatory thresholds ($10,000). |
| **Mule Account Detection** | Dynamic risk scoring ($0-100$), automated account ranking, and **Explainable AI (XAI)** indicator contribution breakdown explaining every score. |
| **Money Trail Analysis** | Multi-hop directed fund movement tracing (Victim -> Mule 1 -> Mule 2 -> Cashout), identifying intermediary layering accounts and ATM cashout nodes. |
| **Complaint Correlation** | Direct correlation of victim cybercrime complaints (e.g. I4C / IC3) with banking transaction trails, automatically linking reports to suspect networks. |
| **Graph-Based Investigation** | GPU-accelerated Cytoscape graph visualizer rendering account relationships, clusters, and shared-device rings with sorted Left-to-Right pipeline flow. |
| **Investigation Dashboard** | Law enforcement investigation workspace with prioritized alert triage, interactive graph pivoting, and evidence dossier export. |
| **Testing Unknown Data** | Ingestion of raw unseen records directly from the 800MB dataset + an interactive Custom Transaction Injector modal for testing edge cases. |
| **Active Learning (Continuous Feedback)** | Human-in-the-Loop feedback mechanism allowing investigators to confirm mules or mark false alarms for continuous model adaptation. |

---

## Tech Stack & Architecture

* **Backend**: Python 3.12, FastAPI, Uvicorn
* **AI / Machine Learning**: Scikit-Learn (`HistGradientBoostingClassifier`, `RobustScaler`, calibrated probabilities)
* **Graph Analytics**: NetworkX (multi-hop traversal, in/out degree, cycle detection, entity resolution)
* **Frontend**: HTML5, Vanilla CSS (Enterprise Slate Forensic Dark Theme), Cytoscape.js, Vanilla JavaScript
* **Database & Security**: SQLite, SQLAlchemy ORM, JWT Authentication, Argon2 / Bcrypt

---

## Quick Setup & Execution

### 1. Activate the Virtual Environment
```powershell
.venv\Scripts\activate
```

### 2. Run the Application Server
```powershell
python run.py
```
*(Or simply double-click `run.bat` to launch the server and automatically open the dashboard)*

### 3. Open the Dashboard & Swagger Docs
* **Forensic Investigation Dashboard**: [http://localhost:8001/dashboard](http://localhost:8001/dashboard)
* **Interactive API Documentation (Swagger)**: [http://localhost:8001/api/docs](http://localhost:8001/api/docs)
* **API Health Check**: [http://localhost:8001/api/health](http://localhost:8001/api/health)

---

## Core Forensic Capabilities

### 1. Interactive Graph Pivoting
Clicking any node in the transaction network immediately triggers the AI risk engine on that account and re-centers the money trail around it.

### 2. Testing Unknown & Out-of-Distribution Data
* **Ingest 800MB CSV**: Pulls random, completely unseen rows directly from `financial_fraud_detection_dataset.csv` into the active graph to test how the model behaves on real, un-curated data.
* **Inject Log Modal**: Allows investigators to manually type arbitrary accounts, amounts, velocity scores, and device hashes to test edge cases (e.g. high-value legitimate payroll vs. sleeper mules).

### 3. Live Cybercrime Attack Simulator
Simulate realistic bank transaction flows on demand:
* **Layering Attack**: Simulates victim phishing loss followed by rapid multi-hop dispersal across mules into ATM withdrawals within 6 minutes.
* **Smurfing Attack**: Simulates multiple structured deposits just under $10,000 to evade regulatory reporting.
* **Normal Stream**: Simulates clean everyday retail banking baseline.

### 4. Human-in-the-Loop Active Learning Feedback
Investigators can click `[Confirm Mule Account]` or `[Mark False Positive]`, storing training signals to adapt detection thresholds.
