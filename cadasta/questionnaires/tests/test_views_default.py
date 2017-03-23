import json
import pytest
from django.http import Http404
from django.test import TestCase
from django.core.urlresolvers import reverse
from tutelary.models import Policy, assign_user_policies
from skivvy import ViewTestCase

from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from .factories import PDFFormFactory, QuestionnaireFactory
from resources.tests.utils import clear_temp  # noqa
from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from ..views import default
from .. import forms
from ..models import PDFForm
from ..managers import create_children


def assign_policies(user):
    clauses = {
        'clause': [
            {
                'effect': 'allow',
                'object': ['project/*/*'],
                'action': ['pdfform.*']
            },
            {
                'effect': 'allow',
                'object': ['pdfform/*/*/*'],
                'action': ['pdfform.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='allow',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class PDFFormListTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PDFFormList
    template = 'questionnaires/form_list.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.pdfforms = PDFFormFactory.create_batch(2, project=self.project)

    def setup_template_context(self):
        return {'object': self.project, 'pdfform_list': self.pdfforms}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to view this pdf form"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class PDFFormAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PDFFormAdd
    template = 'questionnaires/form_add_new.html'
    success_url_name = 'questionnaires:pdf_form_list'

    def setup_models(self):
        user = UserFactory.create()
        assign_policies(user)
        self.project = ProjectFactory.create()
        self.questionnaire = QuestionnaireFactory.create(project=self.project)

    def setup_template_context(self):
        user = UserFactory.create()
        return {
            'object': self.project,
            'has_questionnaire': True,
            'form': forms.PDFFormCreateForm(contributor=user,
                                            project_id=self.project.id,
                                            questionnaire=self.questionnaire)
        }

    def setup_post_data(self):
        return {
            'name': 'Some name',
            'description': 'Some Description',
            'file': '',
            'instructions': 'Some instructions',
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add a pdf form "
                "to this project"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert PDFForm.objects.count() == 1
        pdfform_created = PDFForm.objects.first()
        assert pdfform_created.name == 'Some name'
        assert pdfform_created.description == 'Some Description'
        assert response.status_code == 302
        assert response.location == self.expected_success_url

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert PDFForm.objects.count() == 0
        assert response.status_code == 302
        assert ("You don't have permission to add a pdf form "
                "to this project"
                in response.messages)

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert PDFForm.objects.count() == 0
        assert response.status_code == 302
        assert '/account/login/' in response.location


class PDFFormAddWithNonExistenceQuestionnaireTest(ViewTestCase,
                                                  UserTestCase, TestCase):
    view_class = default.PDFFormAdd
    template = 'questionnaires/form_add_new.html'
    success_url_name = 'questionnaires:pdf_form_list'

    def setup_models(self):
        user = UserFactory.create()
        assign_policies(user)
        self.project = ProjectFactory.create()

    def setup_template_context(self):
        user = UserFactory.create()
        return {
            'object': self.project,
            'has_questionnaire': False,
            'form': forms.PDFFormCreateForm(contributor=user,
                                            project_id=self.project.id,
                                            questionnaire=None)
        }

    def setup_post_data(self):
        return {
            'name': 'Some name',
            'description': '',
            'file': '',
            'instructions': 'Some instructions',
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content


class PDFFormDetailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PDFFormDetails
    template = 'questionnaires/form_detail.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.pdfform = PDFFormFactory.create(project=self.project)

    def setup_template_context(self):
        return {'object': self.project,
                'can_edit': True,
                'can_delete': True,
                'can_generate': True,
                'pdfform': self.pdfform}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'form': self.pdfform.id
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_form(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'form': 'abc123'})

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to view this pdf form"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class PDFFormDeleteTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PDFFormDelete
    template = 'questionnaires/modal_delete.html'
    success_url_name = 'questionnaires:pdf_form_list'
    post_data = {}

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.pdfform = PDFFormFactory.create(project=self.project)

    def setup_template_context(self):
        return {'object': self.project,
                'can_edit': True,
                'can_delete': True,
                'can_generate': True,
                'pdfform': self.pdfform}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'form': self.pdfform.id
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to delete this pdf form"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_pdfform(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'form': 'abc123'})

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        assert PDFForm.objects.count() == 0

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to delete this pdf form"
                in response.messages)

        assert PDFForm.objects.count() == 1

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        assert PDFForm.objects.count() == 1


class PDFFormEditTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PDFFormEdit
    template = 'questionnaires/form_edit.html'
    success_url_name = 'questionnaires:pdf_form_view'

    post_data = {
        'name': 'Sample PDF Form',
        'instructions': 'Test Instructions',
        'descriptions': 'Test Descriptions',
    }

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.pdfform = PDFFormFactory.create(project=self.project)

    def setup_template_context(self):
        return {'object': self.project,
                'pdfform': self.pdfform,
                'cancel_url': reverse(
                    'questionnaires:pdf_form_view',
                    kwargs={
                        'organization': self.project.organization.slug,
                        'project': self.project.slug,
                        'form': self.pdfform.id,
                    }
                ),
                'form': forms.PDFFormCreateForm(instance=self.pdfform)}

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'form': self.pdfform.id
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'form': self.pdfform.id
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to edit this pdf form"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_from_non_existent_project(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'project': 'abc123'})

    def test_get_non_existent_pdfform(self):
        user = UserFactory.create()
        assign_policies(user)
        with pytest.raises(Http404):
            self.request(user=user, url_kwargs={'form': 'abc123'})

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert response.location == self.expected_success_url

        # attributes field is deferred so we fetch a fresh instance
        pdfform = PDFForm.objects.get(id=self.pdfform.id)
        assert pdfform.name == self.post_data['name']

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to edit this pdf form"
                in response.messages)

        self.pdfform.refresh_from_db()
        assert self.pdfform.name != self.post_data['name']

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.pdfform.refresh_from_db()
        assert self.pdfform.name != self.post_data['name']


class PDFFormDownloadTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PDFFormDownload

    def setup_models(self):
        self.project = ProjectFactory.create()
        self.questionnaire = QuestionnaireFactory.create(project=self.project)
        children = [{
            'label': 'This form showcases the different question',
            'name': 'intro',
            'type': 'note'
        }, {
            'label': 'Text question type',
            'name': 'text_questions',
            'type': 'group',
            'children': [
                {
                    'hint': 'Can be short or long but '
                            'always one line (type = '
                            'text)',
                    'label': 'Text',
                    'name': 'my_string',
                    'type': 'text'
                }
            ],
        }]
        create_children(children, kwargs={'questionnaire': self.questionnaire})
        self.pdfform = PDFFormFactory.create(project=self.project)
        self.user = UserFactory.create()

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'form': self.pdfform.id
        }

    def setup_success_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'form': self.pdfform.id
        }

    def test_get_with_authorized_user(self):
        assign_policies(self.user)
        response = self.request(user=self.user, method='GET')
        assert response.status_code == 200
        assert (response.headers['content-disposition'][1] ==
                'attachment; filename={}.pdf'.format(self.pdfform.name))
        assert (response.headers['content-type'][1] == 'application/pdf')

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.user, method='GET')
        assert response.status_code == 302
        assert ("You don't have permission to generate pdf forms "
                "for this project"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request(method='GET')
        assert response.status_code == 302
        assert '/account/login/' in response.location
