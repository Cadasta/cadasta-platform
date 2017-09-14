from celery import Celery
from django.conf import settings

from cadasta.workertoolbox.conf import Config


conf = Config(
    broker_transport=settings.CELERY_BROKER_TRANSPORT,
    broker_transport_options=getattr(
        settings, 'CELERY_BROKER_TRANSPORT_OPTIONS', {}),
)
app = Celery()
app.config_from_object(conf)
