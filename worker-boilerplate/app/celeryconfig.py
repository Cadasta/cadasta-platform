import os
from kombu import Exchange, Queue

if os.environ.get('SQS', True):
    # Broker settings.
    broker_transport = 'sqs'
    broker_transport_options = {
        'region': 'us-west-2',
        'queue_name_prefix': '{}-'.format(os.environ.get('QUEUE_PREFIX', 'dev'))
    }
    worker_prefetch_multiplier = 0  # https://github.com/celery/celery/issues/3712  # noqa

# List of modules to import when the Celery worker starts.
imports = ('app.tasks',)
QUEUE_NAME = 'export'

# Exchanges
task_default_exchange = 'task_exchange'
task_default_exchange_type = 'topic'
result_exchange = 'result_exchange'
result_exchange_type = 'topic'
default_exchange_obj = Exchange(task_default_exchange, task_default_exchange_type)
result_exchange_obj = Exchange(result_exchange, result_exchange_type)

# Queues
task_default_queue = 'scheduled_tasks.fifo'
result_queue = 'result_queue.fifo'  # Custom variable
task_queues = (
    # Queue being processed by this worker
    Queue(QUEUE_NAME, default_exchange_obj, routing_key=QUEUE_NAME),

    # Queue for scheduled tasks
    Queue(task_default_queue, default_exchange_obj, routing_key='#'),

    # Queue for results
    Queue(result_queue, result_exchange_obj, routing_key='#'),
)

# Routing
task_routes = {
    # Associate specific task names or task name patterns to an exchange
    # and routing key
    'export.*': {
        'exchange': default_exchange_obj,
        'routing_key': 'export',
    },
}

# Tasks
task_track_started = True
