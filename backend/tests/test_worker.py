from app.workers.celery_app import celery_app, create_celery
from app.workers.tasks import ping


def test_celery_uses_json_only_and_late_acks() -> None:
    conf = celery_app.conf

    assert conf.task_serializer == "json"
    assert conf.accept_content == ["json"]
    assert conf.task_acks_late is True
    assert conf.task_reject_on_worker_lost is True
    assert conf.worker_prefetch_multiplier == 1


def test_celery_uses_configured_redis(settings: object) -> None:
    app = create_celery(settings)  # type: ignore[arg-type]

    assert app.conf.broker_url == "redis://localhost:6379/15"


def test_ping_task_is_registered_and_runs() -> None:
    assert "devvault.system.ping" in celery_app.tasks

    result = ping.apply()

    assert result.successful()
    assert result.get() == {"status": "ok", "service": "devvault-worker"}
