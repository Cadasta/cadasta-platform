from django.test import TestCase
from ..widgets import XLangSelect


class XLangSelectTest(TestCase):
    def test_set_xlang_labels(self):
        xlang_labels = {'field': {'en': 'Field', 'de': 'Feld'}}
        widget = XLangSelect(xlang_labels=xlang_labels)

        option_groups = [(None, [{'value': 'field', 'attrs': {}}], 0)]

        updated_option_groups = widget.set_xlang_labels(option_groups)
        assert updated_option_groups[0][1][0]['attrs'] == {
            'data-label-en': 'Field',
            'data-label-de': 'Feld'
        }
