from django.test import TestCase
from ..templatetags.tags import define


class FilterTest(TestCase):
    def test_val(self):
        """Tag function should return the same value"""
        assert define('Blah') == 'Blah'

    def test_val_undefined(self):
        """If value is not defined tag function should return None"""
        assert define() is None
