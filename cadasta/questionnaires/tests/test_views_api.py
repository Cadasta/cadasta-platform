import json
import pytest
from django.test import TestCase

from tutelary.models import Policy
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from ..views import api
from ..models import Questionnaire
from .factories import QuestionnaireFactory


@pytest.mark.usefixtures('make_dirs')
class QuestionnaireDetailTest(APITestCase, UserTestCase,
                              FileStorageTestCase, TestCase):
    view_class = api.QuestionnaireDetail

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

    def test_get_questionnaire_as_xform(self):
        questionnaire = QuestionnaireFactory.create(project=self.prj)
        response = self.request(user=self.user, get_data={'format': 'xform'})
        assert response.status_code == 200
        assert (response.headers['content-type'][1] ==
                'application/xml; charset=utf-8')
        assert '<{id} id="{id}" version="{v}"/>'.format(
                id=questionnaire.id_string,
                v=questionnaire.version) in response.content

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
        data = {'xls_form': self.get_form('xls-form')}
        response = self.request(method='PUT', user=self.user, post_data=data)
        assert response.status_code == 201
        assert response.content.get('xls_form') == data['xls_form']
        assert Questionnaire.objects.filter(project=self.prj).count() == 1

    def test_create_questionnaire_with_unauthorized_user(self):
        data = {'xls_form': self.get_form('xls-form')}
        user = UserFactory.create()
        response = self.request(method='PUT', user=user, post_data=data)
        assert response.status_code == 403
        assert Questionnaire.objects.filter(project=self.prj).count() == 0

    def test_create_invalid_questionnaire(self):  #
        data = {'xls_form': self.get_form('xls-form-invalid')}
        response = self.request(method='PUT', post_data=data, user=self.user)

        assert ("Unknown question type 'interger'." in
                response.content.get('xls_form'))
        assert Questionnaire.objects.filter(project=self.prj).count() == 0

    def test_create_with_blocked_questionnaire_upload(self):
        data = {'xls_form': self.get_form('xls-form')}
        SpatialUnitFactory.create(project=self.prj)
        response = self.request(method='PUT', user=self.user, post_data=data)

        assert response.status_code == 400
        assert ("Data has already been contributed to this "
                "project. To ensure data integrity, uploading a "
                "new questionnaire is diabled for this project." in
                response.content.get('xls_form'))

    def test_create_valid_questionnaire_from_json(self):
        data = {
            'title': 'yx8sqx6488wbc4yysnkrbnfq',
            'id_string': 'yx8sqx6488wbc4yysnkrbnfq',
            'questions': [{
                'name': "start",
                'label': "Start",
                'type': "ST",
                'required': False,
                'constraint': None
            }, {
                'name': "end",
                'label': "end",
                'type': "EN",
            }]
        }
        response = self.request(method='PUT', post_data=data, user=self.user)

        assert response.status_code == 201
        assert Questionnaire.objects.filter(project=self.prj).count() == 1
        assert response.content['title'] == data['title']
        self.prj.refresh_from_db()
        assert self.prj.current_questionnaire == response.content['id']

    def test_create_invalid_questionnaire_from_json(self):
        data = {
            'id_string': 'yx8sqx6488wbc4yysnkrbnfq',
        }
        response = self.request(method='PUT', post_data=data, user=self.user)

        assert response.status_code == 400
        assert Questionnaire.objects.filter(project=self.prj).count() == 0
        assert response.content['title'] == ['This field is required.']
        self.prj.refresh_from_db()
        assert self.prj.current_questionnaire is None
