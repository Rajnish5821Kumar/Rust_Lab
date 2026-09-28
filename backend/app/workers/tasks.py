from app.workers.celery_app import celery_app


@celery_app.task(name="devvault.system.ping")  # type: ignore[untyped-decorator]
def ping() -> dict[str, str]:
    """Round-trip check that a worker is consuming from the broker."""
    return {"status": "ok", "service": "devvault-worker"}
