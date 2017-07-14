"""Unit tests for django-picklefield."""
import pickle
from itertools import chain
from unittest.mock import patch, MagicMock

from django.test import TestCase

from tasks.fields import PickledObjectField


TEST_DATA = [
    (None, None),
    (memoryview(pickle.dumps('hello')), 'hello'),
    (memoryview(pickle.dumps({'a': 1})), {'a': 1}),
    (memoryview(pickle.dumps(['a', 1])), ['a', 1]),
    (memoryview(pickle.dumps(('a', 1))), ('a', 1)),
    (memoryview(pickle.dumps({'a', 1})), {'a', 1}),
]


class PickledObjectFieldTests(TestCase):

    def test_to_python(self):
        for (data_in, exp_out) in TEST_DATA:
            assert PickledObjectField().to_python(data_in) == exp_out

    def test_from_db_value(self):
        for (data_in, exp_out) in TEST_DATA:
            out = PickledObjectField().from_db_value(data_in, None, None, None)
            assert out == exp_out

    def test_get_db_prep_value(self):
        for (_, data_in) in TEST_DATA:
            module = 'tasks.fields.models.BinaryField.get_db_prep_value'
            with patch(module) as func:
                PickledObjectField().get_db_prep_value(data_in)
                exp_out = pickle.dumps(data_in)
                func.assert_called_once_with(exp_out, None, False)

    def test_value_to_string(self):
        for (exp_out, data_in) in TEST_DATA:
            with patch.object(PickledObjectField, 'get_db_prep_value') as mock:
                obj = MagicMock(foo=data_in)
                f = PickledObjectField()
                f.attname = 'foo'
                mock.return_value = exp_out
                assert f.value_to_string(obj) == exp_out
                f.get_db_prep_value.assert_called_once_with(data_in)

    def test_get_lookup(self):
        good = ['exact', 'in', 'isnull']
        bad = ['gte', 'lte']
        tests = chain([(l, True) for l in good], [(l, False) for l in bad])

        for lookup, allowed in tests:
            with patch('tasks.fields.models.BinaryField.get_lookup') as func:
                f = PickledObjectField()
                if allowed:
                    f.get_lookup(lookup)
                    func.assert_called_once_with(lookup)
                else:
                    with self.assertRaises(TypeError):
                        f.get_lookup(lookup)
                        assert func.call_count == 0
