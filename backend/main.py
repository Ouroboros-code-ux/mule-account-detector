import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

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
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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