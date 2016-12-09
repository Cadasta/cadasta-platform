from django.test import TestCase
from ..widgets import XLangSelect


class XLangSelectTest(TestCase):
    def test_render_option(self):
        xlang_labels = {'field': {'en': 'Field', 'de': 'Feld'}}
        widget = XLangSelect(xlang_labels=xlang_labels)
        option = widget.render_option([], 'field', 'Feld')
        assert 'data-label-en="Field"' in option
        assert 'data-label-de="Feld"' in option
