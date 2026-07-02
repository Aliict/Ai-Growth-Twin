from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    advisor,
    analytics,
    dashboard,
    experiments,
    funnel,
    growth_twin,
    revenue,
    revenue_leaks,
    roadmap,
    simulator,
)
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(funnel.router)
app.include_router(analytics.router)
app.include_router(revenue.router)
app.include_router(revenue_leaks.router)
app.include_router(experiments.router)
app.include_router(simulator.router)
app.include_router(advisor.router)
app.include_router(roadmap.router)
app.include_router(growth_twin.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
