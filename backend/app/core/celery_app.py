"""Celery configuration is optional until a broker is configured and installed."""

from app.core.config import settings

try:
    from celery import Celery
except ImportError:  # API remains runnable without the optional worker dependency.
    celery_app = None
else:
    celery_app = Celery("comp_hub", broker=settings.redis_url, backend=settings.redis_url.rsplit("/", 1)[0] + "/1")
    celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"], timezone="UTC")

__all__ = ["celery_app"]
