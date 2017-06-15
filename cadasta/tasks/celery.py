from celery import Celery

app = Celery()
# app.conf.worker_consumer = 'tasks.consumers:ResultConsumer'
# app.conf.result_backend = 'tasks.backends:ResultQueueRPC'
app.config_from_object('django.conf:settings', namespace='CELERY')

# from celery import bootsteps

# class InfoStep(bootsteps.Step):

#     def __init__(self, parent, **kwargs):
#         # here we can prepare the Worker/Consumer object
#         # in any way we want, set attribute defaults, and so on.
#         print('{0!r} is in init'.format(parent))

#     def start(self, parent):
#         # our step is started together with all other Worker/Consumer
#         # bootsteps.
#         print('{0!r} is starting'.format(parent))

#     def stop(self, parent):
#         # the Consumer calls stop every time the consumer is
#         # restarted (i.e., connection is lost) and also at shutdown.
#         # The Worker will call stop at shutdown only.
#         print('{0!r} is stopping'.format(parent))

#     def shutdown(self, parent):
#         # shutdown is called by the Consumer at shutdown, it's not
#         # called by Worker.
#         print('{0!r} is shutting down'.format(parent))


# class WorkerStep(bootsteps.Step):
#     def start(self, worker):
#         print("FOOBAR")
#         from celery.contrib import rdb
#         rdb.set_trace()
#         for task in [t for t in self.app.tasks]:
#             if not task.startswith('result_consumer'):
#                 self.app.tasks.unregister(task)
#                 print("Rm {!r}".format(task))

# app.steps['worker'].add(WorkerStep)
# app.steps['consumer'].add(InfoStep)
