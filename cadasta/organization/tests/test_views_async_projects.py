import json
import pytest

from accounts.tests.factories import UserFactory
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from skivvy import ViewTestCase
from tutelary.models import Policy, Role

from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from organization.models import OrganizationRole, ProjectRole
from party.tests.factories import PartyFactory
from questionnaires.models import Questionnaire
from resources.tests.factories import ResourceFactory
from spatial.tests.factories import SpatialUnitFactory

from .factories import OrganizationFactory, ProjectFactory, clause
from ..views import async


class ProjectDashboardTest(FileStorageTestCase, ViewTestCase, UserTestCase,
                           TestCase):
    view_class = async.ProjectDashboard
    template = 'organization/project_dashboard.html'

    def setup_models(self):
        self.project = ProjectFactory.create()
        clauses = {
            'clause': [
                clause('allow',
                       ['project.list'],
                       ['organization/*']),
                clause('allow',
                       ['project.view', 'project.view_private'],
                       ['project/*/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        self.user.assign_policies(self.policy)

    def setup_template_context(self):
        return {
            'object': self.project,
            'project': self.project,
            'is_superuser': False,
            'is_administrator': False,
            'has_content': False,
            'num_locations': 0,
            'num_parties': 0,
            'num_resources': 0,
            'is_allowed_add_location': False,
            'is_allowed_add_resource': False,
            'is_project_member': False,
            'is_allowed_add_resource': False
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_superuser(self):
        superuser_role = Role.objects.get(name='superuser')
        self.user.assign_policies(superuser_role)
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(is_superuser=True,
                                       is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_project_member=True,
                                       is_allowed_import=True)
        assert response.content == expected

    def test_get_with_org_admin(self):
        OrganizationRole.objects.create(
            organization=self.project.organization,
            user=self.user,
            admin=True
        )
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_project_member=True,
                                       is_allowed_import=True)
        assert response.content == expected

    def test_get_with_project_manager(self):
        ProjectRole.objects.create(
            project=self.project,
            user=self.user,
            role='PM',
        )
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_project_member=True,
                                       is_allowed_import=True)
        assert response.content == expected

    def test_get_non_existent_project(self):
        with pytest.raises(Http404):
            self.request(
                user=self.user,
                url_kwargs={'organization': 'some-org', 'project': 'some=prj'})

    def test_get_with_project_extent(self):
        self.project.extent = (
            'SRID=4326;'
            'POLYGON ((-5.1031494140625000 8.1299292850467957, '
            '-5.0482177734375000 7.6837733211111425, '
            '-4.6746826171875000 7.8252894725496338, '
            '-4.8641967773437491 8.2278005261522775, '
            '-5.1031494140625000 8.1299292850467957))')
        self.project.save()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_private_project(self):
        self.project.access = 'private'
        self.project.save()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_private_project_with_unauthenticated_user(self):
        self.project.access = 'private'
        self.project.save()
        response = self.request()
        assert response.status_code == 302
        assert ("You don't have permission to access this project"
                in response.messages)

    def test_get_private_project_without_permission(self):
        # Note, no project.view_private!
        restricted_clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*']),
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        self.user.assign_policies(restricted_policy)

        self.project.access = 'private'
        self.project.save()
        response = self.request()
        assert response.status_code == 302
        assert ("You don't have permission to access this project"
                in response.messages)

    def test_get_private_project_based_on_org_membership(self):
        OrganizationRole.objects.create(organization=self.project.organization,
                                        user=self.user)
        self.project.access = 'private'
        self.project.save()

        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_private_project_with_other_org_membership(self):
        org = OrganizationFactory.create()
        OrganizationRole.objects.create(organization=org, user=self.user)
        self.project.access = 'private'
        self.project.save()

        response = self.request(user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to access this project"
                in response.messages)

    def test_get_private_project_with_superuser(self):
        self.project.access = 'private'
        self.project.save()

        self.superuser_role = Role.objects.get(name='superuser')
        self.user.assign_policies(self.superuser_role)
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(is_superuser=True,
                                       is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_project_member=True,
                                       is_allowed_import=True)
        assert response.content == expected

    def test_get_archived_project_with_unauthorized_user(self):
        self.project.archived = True
        self.project.save()

        response = self.request()
        assert response.status_code == 302
        assert ("You don't have permission to access this project"
                in response.messages)

    def test_get_archived_project_with_unauthentic_user(self):
        self.project.archived = True
        self.project.save()

        response = self.request(user=AnonymousUser())
        assert response.status_code == 302
        assert ("You don't have permission to access this project"
                in response.messages)

    def test_get_archived_project_with_org_admin(self):
        org_admin = UserFactory.create()
        OrganizationRole.objects.create(
            organization=self.project.organization,
            user=org_admin,
            admin=True
        )
        self.project.archived = True
        self.project.save()
        response = self.request(user=org_admin)
        assert response.status_code == 200
        expected = self.render_content(is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_allowed_import=True,
                                       is_project_member=True)
        assert response.content == expected

    def test_get_with_overview_stats(self):
        SpatialUnitFactory.create(project=self.project)
        PartyFactory.create(project=self.project)
        ResourceFactory.create(project=self.project)
        ResourceFactory.create(project=self.project, archived=True)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.render_content(has_content=True,
                                                       num_locations=1,
                                                       num_parties=1,
                                                       num_resources=1)
        assert "<div class=\"num\">1</div> location" in response.content
        assert "<div class=\"num\">1</div> party" in response.content
        assert "<div class=\"num\">1</div> resource" in response.content

    def test_get_with_labels(self):
        file = self.get_file(
            '/questionnaires/tests/files/ok-multilingual.xlsx', 'rb')
        form = self.storage.save('xls-forms/xls-form.xlsx', file)
        Questionnaire.objects.create_from_form(
            xls_form=form,
            original_file='original.xls',
            project=self.project
        )
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.render_content(
            form_lang_default='en',
            form_langs=[('en', 'English'), ('fr', 'French')])
