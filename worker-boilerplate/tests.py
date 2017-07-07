import unittest
from unittest.mock import patch, MagicMock

from celery import signals, Celery

from cadasta.workertoolbox.conf import Config


class TestConfiguration(unittest.TestCase):

    @classmethod
    @patch('kombu.transport.SQS.Channel.sqs', MagicMock())
    def setUpClass(cls):
        cls.q_name = 'export'
        cls.conf = Config(queues=(cls.q_name,))
        cls.app = Celery()
        cls.app.config_from_object(cls.conf)
        signals.worker_init.send(sender=None)
        cls.channel = cls.app.connection().channel()

    def test_default_exchange_type(self):
        """ Ensure default exchange is topic exchange """
        def_exch = self.app.conf.task_default_exchange
        exch_type = self.channel.typeof(def_exch).type
        self.assertEqual(exch_type, 'topic')

    def test_default_exchange_routing(self):
        """ Ensure default exchange routes tasks to multiple queues """
        exchange = self.app.conf.task_default_exchange
        queues = self.channel.typeof(exchange).lookup(
            self.channel.get_table(exchange),
            exchange, self.q_name, self.app.conf.task_default_queue)
        self.assertEqual(len(queues), 2)
        self.assertTrue(self.q_name in queues)
        self.assertTrue(self.conf.PLATFORM_QUEUE_NAME in queues)

    def test_celery_exchange_routing(self):
        """
        Ensure celery queue and platform queue are registered with default
        exchange
        """
        exchange = self.app.conf.task_default_exchange
        queues = self.channel.typeof(exchange).lookup(
            table=self.channel.get_table(exchange),
            exchange=exchange, routing_key='celery',
            default=self.app.conf.task_default_queue)

        self.assertEqual(len(queues), 2)
        self.assertTrue('celery' in queues)
        self.assertTrue(self.conf.PLATFORM_QUEUE_NAME in queues)

    def test_celery_task_routing(self):
        """ Ensure celery tasks route to celery queue and platform queue """
        options = self.app.amqp.router.route({}, 'celery.chord_unlock')
        self.assertNotIn('queue', options)
        self.assertIn('exchange', options)
        self.assertIn('routing_key', options)
        exchange = options['exchange'].name
        routing_key = options['routing_key']

        queues = self.channel.typeof(exchange).lookup(
            table=self.channel.get_table(exchange),
            exchange=exchange, routing_key=routing_key,
            default=self.app.conf.task_default_queue)
        self.assertEqual(len(queues), 2)
        self.assertTrue('celery' in queues)
        self.assertTrue(self.conf.PLATFORM_QUEUE_NAME in queues)


if __name__ == '__main__':
    unittest.main()
