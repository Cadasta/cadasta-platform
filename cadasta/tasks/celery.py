from celery import Celery


app = Celery()
app.conf.result_backend = 'tasks.backends:ResultQueueRPC'
app.config_from_object('django.conf:settings', namespace='CELERY')
