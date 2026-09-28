from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api import (
    locations,
    simulations,
    observation,
    comparison,
    export,
    datasources,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Geospatial Flood Simulation & HADR Decision-Support Platform API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "delft3d_configured": settings.DELFT3D_IS_CONFIGURED,
        "gee_configured": settings.GEE_IS_CONFIGURED,
    }


# ─────────────────────────────────────────────
# CORS Configuration
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# API Routers
# ─────────────────────────────────────────────

app.include_router(
    locations.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    simulations.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    observation.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    comparison.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    export.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    datasources.router,
    prefix=settings.API_V1_STR,
)


# ─────────────────────────────────────────────
# Local Development
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )