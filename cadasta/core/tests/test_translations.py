from django.test import TestCase
from django.utils import translation
from django.utils.translation import gettext as _


class TranslationTest(TestCase):
    def test_translations(self):
        cur_language = translation.get_language()
        try:
            translation.activate('de')
            assert _("First name") == "Vorname"
        finally:
            translation.activate(cur_language)
