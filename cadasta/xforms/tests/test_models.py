from json import dumps
from django.test import TestCase
from accounts.tests.factories import UserFactory
from questionnaires.tests.factories import QuestionnaireFactory
from ..models import XFormSubmission


class XFormSubmissionTest(TestCase):
    def test_repr(self):
        user = UserFactory.build(username='john')
        questionnaire = QuestionnaireFactory(title='questions')
        json = {'key': 'value'}
        submission = XFormSubmission(id='abc123',
                                     user=user,
                                     questionnaire=questionnaire,
                                     json_submission=json)
        assert repr(submission) == ('<XFormSubmission id=abc123 user=john'
                                    ' questionnaire=questions'
                                    ' json_submission={}>').format(dumps(json))
