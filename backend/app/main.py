import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.analyze import router as analyze_router

app = FastAPI(title="ParcelIQ", version="0.1.0")

# CORS: read allowed origins from env, fall back to localhost for dev
_default_origins = "http://localhost:5173,http://localhost:3000"
_origins = os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
