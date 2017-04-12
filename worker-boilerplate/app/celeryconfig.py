import os
from kombu import Exchange, Queue


result_backend = 'db+postgresql://{user}:{pw}@{host}/cadasta'.format(
    user=os.environ.get('TASK_DB_USER', 'cadasta'),
    pw=os.environ.get('TASK_DB_PASS', 'cadasta'),
    host=os.environ.get('TASK_DB_HOST', 'localhost'),
)

if os.environ.get('SQS', True):
    # Broker settings.
    prefix = os.environ.get('QUEUE_PREFIX', 'dev')
    broker_transport = 'sqs'
    broker_transport_options = {
        'region': 'us-west-2',
        'queue_name_prefix': '{}-'.format(prefix)
    }
    worker_prefetch_multiplier = 0  # https://github.com/celery/celery/issues/3712  # noqa

# List of modules to import when the Celery worker starts.
imports = ('app.tasks',)
QUEUE_NAME = 'export'
TASK_EXCHANGE_NAME = 'task_exchange'
RESULT_EXCHANGE_NAME = 'result_exchange'
PLATFORM_QUEUE_NAME = 'platform.fifo'

# Exchanges
task_default_exchange = TASK_EXCHANGE_NAME
task_default_exchange_type = 'topic'
result_exchange = RESULT_EXCHANGE_NAME
result_exchange_type = 'topic'
default_exchange_obj = Exchange(
    task_default_exchange, task_default_exchange_type)
result_exchange_obj = Exchange(
    result_exchange, result_exchange_type)

# Queues
task_default_queue = PLATFORM_QUEUE_NAME
task_queues = (
    # Queue being processed by this worker
    Queue('celery', default_exchange_obj, routing_key='celery'),
    Queue(QUEUE_NAME, default_exchange_obj, routing_key=QUEUE_NAME),

    # Queue to send a copy of scheduled tasks back to platform
    Queue(PLATFORM_QUEUE_NAME, default_exchange_obj, routing_key='#'),

    # Queue to send a copy of result messages back to platform
    Queue(PLATFORM_QUEUE_NAME, result_exchange_obj, routing_key='#'),
)

# Routing
task_routes = {
    # Associate specific task names or task name patterns to an exchange
    # and routing key
    'export.*': {
        'exchange': default_exchange_obj,
        'routing_key': 'export',
    },
    'celery.*': {
        'exchange': default_exchange_obj,
        'routing_key': 'celery',
    },
}

# Tasks
task_track_started = True
