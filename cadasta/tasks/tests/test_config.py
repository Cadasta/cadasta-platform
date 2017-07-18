from django.test import TestCase

from tasks.celery import app, conf


class TestConfig(TestCase):

    def setUp(self):
        self.channel = app.connection().channel()

    def test_celery_task_routing(self):
        """ Ensure celery tasks route to celery queue and platform queue """
        options = app.amqp.router.route({}, 'celery.chord_unlock')
        assert 'queue' not in options
        assert 'exchange' in options
        assert 'routing_key' in options
        exchange = options['exchange'].name
        routing_key = options['routing_key']

        queues = self.channel.typeof(exchange).lookup(
            table=self.channel.get_table(exchange),
            exchange=exchange, routing_key=routing_key,
            default=app.conf.task_default_queue)
        assert len(queues) == 2
        assert 'celery' in queues
        assert conf.PLATFORM_QUEUE_NAME in queues
