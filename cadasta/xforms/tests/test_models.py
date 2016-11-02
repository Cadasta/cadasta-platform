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
        instanceID = '19f004e7-d16f-49d0-abcc-a73762c6d102'
        submission = XFormSubmission(id='abc123',
                                     user=user,
                                     questionnaire=questionnaire,
                                     instanceID=instanceID,
                                     json_submission=json)
        assert repr(submission) == ('<XFormSubmission id=abc123 user=john'
                                    ' questionnaire=questions'
                                    ' json_submission={json}'
                                    ' instanceID={instance}'
                                    ' spatial_units=[]'
                                    ' parties=[]'
                                    ' tenure_relationships=[]>'
                                    ).format(json=dumps(json),
                                             instance=instanceID)
