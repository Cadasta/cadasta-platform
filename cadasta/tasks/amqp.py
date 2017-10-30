from celery.app.amqp import AMQP
from cadasta.workertoolbox.setup import setup_app

from core import breakers


class CircuitBreakerAMQP(AMQP):
    @breakers.celery
    def send_task_message(self, *args, **kwargs):
        if not getattr(self.app, 'is_set_up', False):
            setup_app(self.app, throw=True)
        return super(CircuitBreakerAMQP, self).send_task_message(
            *args, **kwargs)
