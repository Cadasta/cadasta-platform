from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from tasks.celery import app
from tasks.utils import fields, celery


class TestFields(TestCase):

    def test_is_type(self):
        is_dict = fields.is_type(dict)
        with self.assertRaises(ValidationError):
            is_dict('asdf')
        is_dict(OrderedDict())

        is_list = fields.is_type(list)
        with self.assertRaises(ValidationError):
            is_list({})
        is_list([])

    def test_input_field_default(self):
        assert fields.input_field_default() == {'args': [], 'kwargs': {}}

    def test_validate_input_field(self):
        # Must be dict
        with self.assertRaises(ValidationError):
            fields.validate_input_field([])
        # Must have only 'args' and 'kwargs'
        with self.assertRaises(ValidationError):
            fields.validate_input_field({'args': [], 'kwargs': {}, 'foo': 1})
        # 'args' must be array
        with self.assertRaises(ValidationError):
            fields.validate_input_field({'args': {}, 'kwargs': {}})
        # 'kwargs' must be dict
        with self.assertRaises(ValidationError):
            fields.validate_input_field({'args': [], 'kwargs': []})
        fields.validate_input_field({'args': ['1'], 'kwargs': {'a': 'b'}})
        fields.validate_input_field({'args': ('a',), 'kwargs': {'foo': 'bar'}})


@override_settings(CELERY_TASK_ROUTES={
    'foo.*': {'queue': 'foo_q'},
    'bar.*': {'queue': 'bar_q'}
})
@override_settings(CELERY_TASK_DEFAULT_QUEUE='default-queue')
@override_settings(CELERY_RESULT_QUEUE='result-queue')
class TestCelery(TestCase):

    def setUp(self):
        # Ensure new routes are applied
        app.amqp.flush_routes()
        app.amqp.router = app.amqp.Router()

    def test_apply_default_options_properly_routed(self):
        self.assertEqual(
            celery.apply_default_options({}, 'foo.asdf').get('queue'),
            'foo_q')
        self.assertEqual(
            celery.apply_default_options({}, 'bar.asdf').get('queue'),
            'bar_q')
        self.assertEqual(
            celery.apply_default_options({}, 'asdf.asdf').get('queue'),
            'default-queue')

    def test_apply_default_options_no_override_queue(self):
        """ Ensure specified queue option is not overridden """
        options = {'queue': 'asdf'}
        self.assertEqual(
            celery.apply_default_options(options, 'foo.asdf').get('queue'),
            'asdf')

    def test_apply_default_options_override_reply_to(self):
        """ Ensure reply_to option is always overridden """
        options = {'reply_to': 'asdf'}
        self.assertEqual(
            celery.apply_default_options(options, 'foo.asdf').get('reply_to'),
            'result-queue')
