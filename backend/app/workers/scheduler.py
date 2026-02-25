from celery.schedules import crontab

from backend.app.workers.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "sync-every-5-minutes": {
        "task": "backend.app.workers.tasks.sync_all_accounts",
        "schedule": crontab(minute="*/5"),
    }
}
