import os
import json
import pytest
from django.conf import settings

from buckets.test.storage import FakeS3Storage
from rest_framework.test import APIRequestFactory, force_authenticate
from tutelary.models import Policy

from core.tests.base_test_case import UserTestCase
from core.tests.util import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from ..views import api
from ..models import Questionnaire
from .factories import QuestionnaireFactory

path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class QuestionnaireDetailTest(UserTestCase):
    def setUp(self):
        super().setUp()
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
        self.url = '/v1/organizations/{}/projects/{}/questionnaire/'.format(
            self.org, self.prj
        )

    def _get_form(self, form_name):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb'
        ).read()
        form = storage.save('xls-forms/{}.xlsx'.format(form_name), file)
        return form

    def _get(self, user=None, status=None, project=None):
        if user is None:
            user = self.user
        request = APIRequestFactory().get(self.url)
        force_authenticate(request, user=user)
        response = api.QuestionnaireDetail.as_view()(
            request,
            organization=self.org.slug,
            project=(project or self.prj.slug)).render()
        content = json.loads(response.content.decode('utf-8'))

        if status is not None:
            assert response.status_code == status

        return content

    def _put(self, data, user=None, status=None):
        if user is None:
            user = self.user
        request = APIRequestFactory().put(self.url, data)
        force_authenticate(request, user=user)
        response = api.QuestionnaireDetail.as_view()(
            request,
            organization=self.org.slug,
            project=self.prj.slug).render()
        content = json.loads(response.content.decode('utf-8'))

        if status is not None:
            assert response.status_code == status

        return content

    def test_get_questionnaire(self):
        questionnaire = QuestionnaireFactory.create(project=self.prj)

        content = self._get(status=200)
        assert content['id'] == questionnaire.id

    def test_get_questionnaire_that_does_not_exist(self):  #
        content = self._get(status=404)
        assert content['detail'] == 'Questionnaire not found.'

    def test_get_questionnaire_from_project_that_does_not_exist(self):
        content = self._get(status=404, project='123abc')
        assert content['detail'] == 'Project not found.'

    def test_get_questionnaire_with_unauthorized_user(self):
        QuestionnaireFactory.create(project=self.prj)
        self._get(status=403, user=UserFactory.create())

    def test_create_questionnaire(self):  #
        form = self._get_form('xls-form')
        data = {'xls_form': form}

        content = self._put(data=data, status=201)

        assert content.get('xls_form') == form
        assert Questionnaire.objects.filter(project=self.prj).count() == 1

    def test_create_questionnaire_with_unauthorized_user(self):
        form = self._get_form('xls-form')
        data = {'xls_form': form}

        self._put(data=data, status=403, user=UserFactory.create())
        assert Questionnaire.objects.filter(project=self.prj).count() == 0

    def test_create_invalid_questionnaire(self):  #
        form = self._get_form('xls-form-invalid')

        data = {'xls_form': form}

        content = self._put(data=data, status=400)
        assert ("Unknown question type 'interger'." in
                content.get('xls_form'))
        assert Questionnaire.objects.filter(project=self.prj).count() == 0
