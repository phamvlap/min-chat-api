import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Create the Celery app
app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Update Celery configuration
app.conf.update(
    worker_pool_restarts=True,
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_soft_time_limit=180,  # 180 seconds for soft time limit
    task_time_limit=300,  # 300 seconds for task execution
    task_default_retry_delay=5,  # 5 seconds before retry
    task_max_retries=3,
)

# Celery Beat config
app.conf.beat_schedule = {}
