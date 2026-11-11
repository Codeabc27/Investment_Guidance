from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import profile
from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.goals import router as goals_router
from app.api.market import router as market_router
from app.api.risk import router as risk_router
from app.api.what_if import router as what_if_router
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(auth_router)
app.include_router(goals_router)
app.include_router(analysis_router)
app.include_router(market_router)
app.include_router(what_if_router)
app.include_router(chat_router)
app.include_router(profile.router)
app.include_router(risk_router)


@app.get("/")
def root():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
