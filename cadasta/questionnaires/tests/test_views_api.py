import os
import json
import pytest
from django.conf import settings
from django.test import TestCase

from tutelary.models import Policy
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from ..views import api
from ..models import Questionnaire
from .factories import QuestionnaireFactory
from .utils import get_form

path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class QuestionnaireDetailTest(APITestCase, UserTestCase, TestCase):
    view_class = api.QuestionnaireDetail

    def setup_post_data(self):
        form = get_form('xls-form')
        return {'xls_form': form}

    def setup_models(self):
        clause = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['project/*/*'],
                    'action': ['questionnaire.*']
                }
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(organization=self.org)

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug
        }

    def test_get_questionnaire(self):
        questionnaire = QuestionnaireFactory.create(project=self.prj)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == questionnaire.id

    def test_get_questionnaire_that_does_not_exist(self):
        response = self.request(user=self.user)
        assert response.status_code == 404
        assert response.content['detail'] == 'Questionnaire not found.'

    def test_get_questionnaire_from_project_that_does_not_exist(self):
        response = self.request(user=self.user, url_kwargs={'project': 'a'})
        assert response.status_code == 404
        assert response.content['detail'] == 'Project not found.'

    def test_get_questionnaire_with_unauthorized_user(self):
        user = UserFactory.create()
        QuestionnaireFactory.create(project=self.prj)
        response = self.request(user=user)
        assert response.status_code == 403

    def test_create_questionnaire(self):
        response = self.request(method='PUT', user=self.user)
        assert response.status_code == 201
        assert (response.content.get('xls_form') ==
                self.setup_post_data()['xls_form'])
        assert Questionnaire.objects.filter(project=self.prj).count() == 1

    def test_create_questionnaire_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='PUT', user=user)
        assert response.status_code == 403
        assert Questionnaire.objects.filter(project=self.prj).count() == 0

    def test_create_invalid_questionnaire(self):  #
        data = {'xls_form': get_form('xls-form-invalid')}
        response = self.request(method='PUT', post_data=data, user=self.user)

        assert ("Unknown question type 'interger'." in
                response.content.get('xls_form'))
        assert Questionnaire.objects.filter(project=self.prj).count() == 0
