from celery.signals import before_task_publish

from .models import BackgroundTask
from .utils.celery import apply_default_options


@before_task_publish.connect
def create_model(sender, headers, body, properties, **kw):
    """ Create BackgroundTask models from tasks scheduled by Celery """
    args, kwargs, options = body

    # Add default properties
    option_keys = ['eta', 'expires', 'retries', 'timelimit']
    properties.update(
        **{k: v for k, v in headers.items()
           if k in option_keys and v not in (None, [None, None])},
        **apply_default_options(properties, headers['task']))

    # Ensure chained tasks contain proper data
    parent_id = headers['id']
    chain = options.get('chain') or []
    for t in chain[::-1]:  # Chain array comes in reverse order
        t.parent_id = parent_id
        parent_id = t.id
        t.options = apply_default_options(t.options, t.name)

    # TODO: Add support for grouped tasks

    BackgroundTask.objects.bulk_create([
        BackgroundTask(
            id=headers['id'],
            type=headers['task'],
            input_args=args,
            input_kwargs=kwargs,
            options=properties,
        ),
        *[BackgroundTask(
            id=t.id,
            type=t.task,
            input_args=t.args,
            input_kwargs=t.kwargs,
            parent_id=t.parent_id,
            root_id=headers['id'],
            immutable=t.immutable,
            options=t.options,
        ) for t in chain]
    ])
