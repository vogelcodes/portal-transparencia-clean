from celery import Celery
import os

celery_app = Celery(
    'tasks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

@celery_app.task
def hello():
    return 'Hello from worker!'

@celery_app.task
def placeholder():
    return {'status': 'pending'}
</TEXT>