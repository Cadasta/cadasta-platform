import os

if os.environ.get('SQS'):
    # Broker settings.
    broker_transport = 'sqs'
    broker_transport_options = {
        'region': 'us-west-2',
    }
    assert os.environ.get('QUEUE_PREFIX'), (
        "Must set 'QUEUE_PREFIX' env variable")
    prefix = '{}-'.format(os.environ['QUEUE_PREFIX'])
    broker_transport_options.update(queue_name_prefix=prefix)
    worker_prefetch_multiplier = 0  # https://github.com/celery/celery/issues/3712  # noqa

# List of modules to import when the Celery worker starts.
imports = ('app.tasks',)

# Place results back into queue.
result_backend = 'rpc://'
task_track_started = True
