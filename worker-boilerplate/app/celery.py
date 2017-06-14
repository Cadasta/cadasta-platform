from __future__ import absolute_import

from celery import Celery


app = Celery('app',
             task_cls='app.celeryutils.Task',
             backend='app.celeryutils.ResultQueueRPC',)
app.config_from_object('app.celeryconfig')

# TODO: Mv to signal
p = app.amqp.producer_pool.acquire()
try:
    # Ensure all queues are registered with proper exchanges
    [p.maybe_declare(q) for q in app.amqp.queues.values()]
finally:
    p.release()


if __name__ == '__main__':
    app.start()
