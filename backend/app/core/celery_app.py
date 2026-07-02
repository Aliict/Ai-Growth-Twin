from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "growth_twin",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.growth_twin_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "refresh-growth-twin-snapshot": {
            "task": "app.tasks.growth_twin_tasks.refresh_growth_twin_snapshot",
            "schedule": 3600.0,
        },
    },
)
