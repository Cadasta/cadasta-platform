from django.test import TestCase

from ..exceptions import JsonValidationError


class JsonValidationErrorTest(TestCase):
    def test_to_string(self):
        exc = JsonValidationError({
            'field': "Some error"
        })

        assert str(exc) == '{"field": "Some error"}'
