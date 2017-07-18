from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.test import TestCase

from tasks.utils import fields


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
