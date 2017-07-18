import logging

from django.core.management.base import BaseCommand
from kombu import Queue
from kombu.async import Hub, set_event_loop

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
        with app.connection() as conn:
            try:
                logger.info("Launching worker")
                worker = Worker(conn, queues=[Queue(queue)])
                worker.run()
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt, exiting. Bye!")
