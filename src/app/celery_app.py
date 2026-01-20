from celery import Celery

from .config import Config

celery_app = Celery(
    'deribit_tracker',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=['app.tasks.fetch_prices'],
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'fetch-prices-every-minute': {
            'task': 'app.tasks.fetch_prices.fetch_prices_task',
            'schedule': 60.0,
        },
    },
)
