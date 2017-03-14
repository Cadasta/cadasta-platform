from django.test import TestCase
from ..exceptions import InvalidQuestionnaire


class InvalidQuestionnaireTest(TestCase):
    def test_str(self):
        exc = InvalidQuestionnaire(errors=['E 1', 'E 2'])
        assert str(exc) == 'E 1, E 2'
