"""Celery application. Start a worker with: celery -A app.workers.celery_app worker"""

from celery import Celery

from app.core.config import Settings, get_settings


def create_celery(settings: Settings) -> Celery:
    app = Celery(
        "devvault",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["app.workers.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        # Tasks are written to be idempotent, so redelivery after a worker crash is safe
        # and preferable to silently losing work.
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        result_expires=60 * 60 * 24,
        broker_connection_retry_on_startup=True,
    )
    return app


celery_app = create_celery(get_settings())
