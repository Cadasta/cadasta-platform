from django.test import TestCase
from django.utils.translation import activate
from ..functions import select_multilang_field_label


class SelectMultilangFieldLabelTest(TestCase):
    def test_normal_string_label(self):
        assert select_multilang_field_label("Label") == "Label"

    def test_default_from_multilanguage_label(self):
        label = '{"default": "Label", "Deutsch": "Etikett"}'
        assert select_multilang_field_label(label) == "Label"

    def test_lang_code_from_multilanguage_label(self):
        activate('de')
        label = '{"default": "Label", "de": "Etikett"}'
        assert select_multilang_field_label(label) == "Etikett"
        activate('en-us')

    def test_lang_name_from_multilanguage_label(self):
        activate('de')
        label = '{"default": "Label", "German": "Etikett"}'
        assert select_multilang_field_label(label) == "Etikett"
        activate('en-us')

    def test_lang_native_name_from_multilanguage_label(self):
        activate('de')
        label = '{"default": "Label", "Deutsch": "Etikett"}'
        assert select_multilang_field_label(label) == "Etikett"
        activate('en-us')
