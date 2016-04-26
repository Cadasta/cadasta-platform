from django.test import TestCase
from ..exceptions import InvalidXLSForm


class InvalidXLSFormTest(TestCase):
    def test_str(self):
        exc = InvalidXLSForm(errors=['E 1', 'E 2'])
        assert str(exc) == 'E 1, E 2'
