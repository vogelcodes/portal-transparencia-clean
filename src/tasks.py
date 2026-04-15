from celery import Celery
from flask import Flask

import os

# Configuração do Celery
celery = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL")),
    backend=os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL")),
)

# Configurações extras
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)

# Função de exemplo - você pode adicionar suas tarefas aqui
@celery.task(name="health_check")
def health_check():
    return {"status": "ok"}
