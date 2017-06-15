from celery import Celery

app = Celery()
app.conf.worker_consumer = 'tasks.consumers:ResultConsumer'
# app.conf.result_backend = 'tasks.backends:ResultQueueRPC'
app.config_from_object('django.conf:settings', namespace='CELERY')
