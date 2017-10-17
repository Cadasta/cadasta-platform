import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from kombu import Queue
from kombu.async import Hub, set_event_loop

from core import breakers
from tasks.celery import app, conf
from tasks.consumer import Worker


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync task and result messages with database."

    def add_arguments(self, parser):
        parser.add_argument('--queue', '-q', default=conf.PLATFORM_QUEUE_NAME)

    def handle(self, queue, *args, **options):
        fmt = '%(asctime)s %(name)-12s: %(levelname)-8s %(message)s'
        log_level = 40 - (options['verbosity'] * 10)
        logging.basicConfig(level=log_level, format=fmt)

        # TODO: Ensure that failed processing does not requeue task into
        # work queue
        set_event_loop(Hub())
        kwargs = {
            'transport_options': settings.CELERY_BROKER_TRANSPORT_OPTIONS,
        }
        with app.connection(**kwargs) as conn:
            logger.info("Launching worker")
            worker = Worker(conn, queues=[Queue(queue)])
            worker.connect_max_retries = 1
            while True:
                try:
                    breakers.celery.call(worker.run)
                except KeyboardInterrupt:
                    logger.info("KeyboardInterrupt, exiting. Bye!")
                    break
                except breakers.celery.expected_errors:
                    rest_val = 5
                    logger.warning(
                        "Open circuit detected. "
                        "Sleeping for %s seconds and then will try again.",
                        rest_val
                    )
                    time.sleep(rest_val)
