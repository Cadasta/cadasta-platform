from celery.signals import worker_init


@worker_init.connect
def setup_exchanges(**kwargs):
    """ Setup result exchange to route all tasks to platform queue """
    from .celery import app
    p = app.amqp.producer_pool.acquire()
    try:
        for q in app.conf.task_queues:
            p.maybe_declare(q)
    finally:
        p.release()
