import unittest

from celery import signals

from app.celery import app
from app.celeryconfig import QUEUE_NAME, PLATFORM_QUEUE_NAME


class TestExchangeConfiguration(unittest.TestCase):

    def setUp(self):
        signals.worker_init.send(sender=None)
        self.channel = app.connection().channel()

    def test_default_exchange_type(self):
        """ Ensure default exchange is topic exchange """
        exch_type = self.channel.typeof(app.conf.task_default_exchange).type
        self.assertEqual(exch_type, 'topic')

    def test_default_exchange_routing(self):
        """ Ensure default exchange routes tasks to multiple queues """
        exchange = app.conf.task_default_exchange
        queues = self.channel.typeof(exchange).lookup(
            self.channel.get_table(exchange),
            exchange, QUEUE_NAME, app.conf.task_default_queue)
        self.assertEqual(len(queues), 2)
        self.assertTrue(QUEUE_NAME in queues)
        self.assertTrue(PLATFORM_QUEUE_NAME in queues)

    def test_celery_exchange_routing(self):
        """
        Ensure celery queue and platform queue are registered with default
        exchange
        """
        exchange = app.conf.task_default_exchange
        queues = self.channel.typeof(exchange).lookup(
            table=self.channel.get_table(exchange),
            exchange=exchange, routing_key='celery',
            default=app.conf.task_default_queue)

        self.assertEqual(len(queues), 2)
        self.assertTrue('celery' in queues)
        self.assertTrue(PLATFORM_QUEUE_NAME in queues)

    def test_celery_task_routing(self):
        """ Ensure celery tasks route to celery queue and platform queue """
        options = app.amqp.router.route({}, 'celery.chord_unlock')
        self.assertNotIn('queue', options)
        self.assertIn('exchange', options)
        self.assertIn('routing_key', options)
        exchange = options['exchange'].name
        routing_key = options['routing_key']

        queues = self.channel.typeof(exchange).lookup(
            table=self.channel.get_table(exchange),
            exchange=exchange, routing_key=routing_key,
            default=app.conf.task_default_queue)
        self.assertEqual(len(queues), 2)
        self.assertTrue('celery' in queues)
        self.assertTrue(PLATFORM_QUEUE_NAME in queues)


if __name__ == '__main__':
    unittest.main()
