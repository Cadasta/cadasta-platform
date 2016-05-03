from django.test import TestCase
from .factories import QuestionFactory


class QuestionTest(TestCase):
    def test_has_options(self):
        question = QuestionFactory.create(type='S1')
        assert question.has_options is True

        question = QuestionFactory.create(type='SM')
        assert question.has_options is True

        question = QuestionFactory.create(type='IN')
        assert question.has_options is False
