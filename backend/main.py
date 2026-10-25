import sys
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

# Add project root to sys.path so imports resolve cleanly in any IDE or runner
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.limiter import limiter
    from backend.database import init_db
    from backend.routers import auth, web, mule_routes, complaint_routes
except ImportError:
    from .limiter import limiter
    from .database import init_db
    from .routers import auth, web, mule_routes, complaint_routes

# Initialize DB for investigator users
init_db()

app = FastAPI(
    title="MuleShield AI: Mule Account & Cybercrime Network Detection Engine",
    description="AI/ML & Graph Analytics solution for detecting money mules, multi-hop layering, and cybercrime money trails.",
    version="2.0.0",
    docs_url="/api/docs"
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please slow down your requests."}
    )

# Mount root directory for static assets
app.mount("/static", StaticFiles(directory="."), name="static")

ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8001,http://127.0.0.1:8001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Core API Routers
app.include_router(auth.router)
app.include_router(web.router)
app.include_router(mule_routes.router)
app.include_router(complaint_routes.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "MuleShield AI",
        "version": "2.0.0",
        "thematic_areas": [
            "Financial Cybersecurity",
            "AI/ML",
            "Graph Analytics",
            "Fraud Detection",
            "Money Trail Investigation",
            "Explainable AI",
            "Complaint Correlation"
        ]
    }