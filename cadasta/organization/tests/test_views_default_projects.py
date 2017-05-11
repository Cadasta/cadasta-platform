import json
import os

import pytest

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.http import Http404, HttpRequest
from django.template.loader import render_to_string
from django.test import TestCase
from jsonattrs.models import Attribute, Schema
from skivvy import remove_csrf
from organization.models import OrganizationRole, Project, ProjectRole
from party.models import Party, TenureRelationship
from party.tests.factories import PartyFactory
from questionnaires.models import Questionnaire
from questionnaires.tests import factories as q_factories
from questionnaires.messages import MISSING_RELEVANT
from resources.models import Resource
from resources.tests.factories import ResourceFactory
from resources.tests.utils import clear_temp  # noqa
from resources.utils.io import ensure_dirs
from skivvy import ViewTestCase
from spatial.models import SpatialUnit
from spatial.tests.factories import SpatialUnitFactory
from tutelary.models import Policy, Role, assign_user_policies

from .. import forms
from ..views import default
from .factories import OrganizationFactory, ProjectFactory, clause


def assign_policies(user):
    clauses = {
        'clause': [
            clause('allow', ['project.*'], ['project/*/*'])
        ]
    }
    policy = Policy.objects.create(name='allow', body=json.dumps(clauses))
    assign_user_policies(user, policy)


class ProjectListTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectList
    template = 'organization/project_list.html'

    def setup_models(self):
        self.ok_org1 = OrganizationFactory.create(name='OK org 1', slug='org1')
        self.ok_org2 = OrganizationFactory.create(name='OK org 2', slug='org2')
        self.unauth_org = OrganizationFactory.create(
            name='Unauthorized org', slug='unauth-org'
        )
        self.projs = []
        self.projs += ProjectFactory.create_batch(2, organization=self.ok_org1)
        self.projs += ProjectFactory.create_batch(2, organization=self.ok_org2)
        self.unauth_projs = []
        self.unauth_projs.append(ProjectFactory.create(
            name='Unauthorized project',
            slug='unauth-proj',
            organization=self.ok_org2
        ))
        self.unauth_projs.append(ProjectFactory.create(
            name='Project in unauthorized org',
            slug='proj-in-unauth-org',
            organization=self.unauth_org
        ))
        self.priv_proj1 = ProjectFactory.create(
            organization=self.ok_org1, access='private'
        )
        self.priv_proj2 = ProjectFactory.create(
            organization=self.ok_org1, access='private'
        )
        self.priv_proj3 = ProjectFactory.create(
            organization=self.ok_org2, access='private'
        )
        self.archived_proj = ProjectFactory.create(
            organization=self.ok_org2, archived=True)
        ProjectFactory.create(organization=self.unauth_org, access='private')

        # Note: no project.view_private -- that's controlled by
        # organization membership in the tests.
        clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*']),
                clause('deny', ['project.view'], ['project/unauth-org/*']),
                clause('deny', ['project.view'], ['project/*/unauth-proj'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assigned_policies = self.user.assigned_policies()
        assigned_policies.append(self.policy)
        self.user.assign_policies(*assigned_policies)

    @property
    def sort_key(self):
        return lambda p: p.organization.slug + ':' + p.slug

    def setup_template_context(self):
        projs = self.projs + self.unauth_projs
        return {
            'object_list': sorted(projs, key=self.sort_key),
            'add_allowed': False,
            'is_superuser': False,
        }

    def test_get_with_valid_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthenticated_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        # Slight weirdness here: an unauthorized user can see *more*
        # projects than a user authorized with the policy defined
        # above because the policy includes clauses denying access to
        # some projects.

        response = self.request(user=UserFactory.create())
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_org_membership(self):
        OrganizationRole.objects.create(organization=self.ok_org1,
                                        user=self.user)
        response = self.request(user=self.user)
        projs = (self.projs + self.unauth_projs +
                 [self.priv_proj1, self.priv_proj2])

        assert response.status_code == 200
        assert response.content == self.render_content(
            object_list=sorted(projs, key=self.sort_key))

    def test_get_with_org_memberships(self):
        OrganizationRole.objects.create(organization=self.ok_org1,
                                        user=self.user)
        OrganizationRole.objects.create(organization=self.ok_org2,
                                        user=self.user)
        response = self.request(user=self.user)
        projs = (self.projs + self.unauth_projs +
                 [self.priv_proj1, self.priv_proj2, self.priv_proj3])

        assert response.status_code == 200
        assert response.content == self.render_content(
            object_list=sorted(projs, key=self.sort_key))

    def test_get_with_org_admin(self):
        OrganizationRole.objects.create(organization=self.ok_org2,
                                        user=self.user,
                                        admin=True,)
        response = self.request(user=self.user)
        projs = (self.projs + self.unauth_projs +
                 [self.priv_proj3, self.archived_proj])

        assert response.status_code == 200
        assert response.content == self.render_content(
            object_list=sorted(projs, key=self.sort_key),
            add_allowed=True)

    def test_get_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)

        response = self.request(user=superuser)
        assert response.status_code == 200
        assert response.content == self.render_content(
            object_list=sorted(Project.objects.all(), key=self.sort_key),
            add_allowed=True,
            is_superuser=True)


class ProjectDashboardTest(FileStorageTestCase, ViewTestCase, UserTestCase,
                           TestCase):
    view_class = default.ProjectDashboard
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
        members = {self.user.username: 'Administrator'}
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_project_member=True,
                                       is_allowed_import=True,
                                       members=members)
        assert response.content == expected

    def test_get_with_project_manager(self):
        role = ProjectRole.objects.create(
            project=self.project,
            user=self.user,
            role='PM',
        )
        response = self.request(user=self.user)
        assert response.status_code == 200
        members = {self.user.username: role.get_role_display()}
        expected = self.render_content(is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_project_member=True,
                                       is_allowed_import=True,
                                       members=members)
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
        members = {org_admin.username: 'Administrator'}
        self.project.archived = True
        self.project.save()
        response = self.request(user=org_admin)
        assert response.status_code == 200
        expected = self.render_content(is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True,
                                       is_allowed_import=True,
                                       is_project_member=True,
                                       members=members)
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
        assert "<span class=\"num\">1</span>" in response.content
        assert "<span class=\"num\">1</span>" in response.content
        assert "<span class=\"num\">1</span>" in response.content

    def test_get_with_labels(self):
        file = self.get_file(
            '/questionnaires/tests/files/ok-multilingual.xlsx', 'rb')
        form = self.storage.save('xls-forms/xls-form.xlsx', file.read())
        file.close()
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


@pytest.mark.usefixtures('make_dirs')
class ProjectAddTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        super().setUp()
        self.view = default.ProjectAddWizard.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        clauses = {
            'clause': [
                clause('allow', ['project.create'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.user = UserFactory.create()
        self.unauth_user = UserFactory.create()
        self.superuser = UserFactory.create()
        self.superuser.assign_policies(Role.objects.get(name='superuser'))

        setattr(self.request, 'user', self.user)
        assign_user_policies(self.user, self.policy)

        self.org = OrganizationFactory.create(
            name='Test Org', slug='test-org'
        )
        self.users = UserFactory.create_from_kwargs([
            {'username': 'org_admin_1'},
            {'username': 'org_admin_2'},
            {'username': 'org_member_1'},
            {'username': 'org_member_2'},
            {'username': 'org_member_3'},
            {'username': 'org_member_4'},
            {'username': 'org_non_member_1'},
            {'username': 'org_non_member_2'},
            {'username': 'org_non_member_3'},
            {'username': 'org_non_member_4'}])
        for idx in range(6):
            OrganizationRole.objects.create(organization=self.org,
                                            user=self.users[idx],
                                            admin=(idx < 2))

    def _get(self, status=None, check_content=False, login_redirect=False):
        response = self.client.get(reverse('project:add'))
        if status is not None:
            assert response.status_code == status
        if login_redirect:
            assert '/account/login/' in response['location']
        if check_content:
            content = response.content.decode('utf-8')
            expected = render_to_string(
                'organization/project_add_extents.html',
                context=response.context_data,
                request=response.wsgi_request
            )
            assert remove_csrf(expected) == remove_csrf(content)

    def test_initial_get_valid(self):
        self.client.force_login(self.user)
        self._get(status=200, check_content=True)

    def test_initial_get_with_unauthorized_user(self):
        self.client.force_login(self.unauth_user)
        self._get(status=200, check_content=True)

    def test_initial_get_with_unauthenticated_user(self):
        self._get(status=302, login_redirect=True)

    def test_get_from_initial_with_org(self):
        """ If users create a project from an organization directly, the
            initial field value will be set the the `organization` value
            provided with the URL kwargs.
        """
        view = default.ProjectAddWizard()
        setattr(view, 'initial_dict', {'details': {}})
        setattr(view, 'kwargs', {'organization': self.org.slug})
        form_initial = view.get_form_initial('details')

        assert form_initial.get('organization') == self.org.slug

    def test_get_from_initial_with_archived_org(self):
        """ If users create a project from an archived organization, if fails.
        """
        self.org.archived = True
        self.org.save()
        self.org.refresh_from_db()
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                'organization:project-add',
                kwargs={'organization': self.org.slug}
            ))
        assert response.status_code == 302
        assert '/projects/new/' not in response['location']

    def test_get_from_initial_with_no_org(self):
        """ If a project is created from scratch, no the initial value for
            `organization must be empty.
        """
        view = default.ProjectAddWizard()
        setattr(view, 'initial_dict', {'details': {}})
        setattr(view, 'kwargs', {})
        form_initial = view.get_form_initial('details')

        assert 'organization' not in form_initial

    EXTENTS_POST_DATA = {
        'project_add_wizard-current_step': 'extents',
        'extents-extent':
        '{"type":"Polygon",'
        '"coordinates":[[[11.524186134338379,47.253077373726235],'
        '[11.524186134338379,47.264669556186654],'
        '[11.544098854064941,47.264669556186654],'
        '[11.544098854064941,47.253077373726235],'
        '[11.524186134338379,47.253077373726235]]]}'
    }
    DETAILS_POST_DATA = {
        'project_add_wizard-current_step': 'details',
        'details-organization': 'test-org',
        'details-name': 'Test Project',
        'details-description': 'This is a test project',
        'details-access': 'on',
        'details-url': 'http://www.test.org',
        'details-contacts-TOTAL_FORMS': 1,
        'details-contacts-INITIAL_FORMS': 0,
        'details-contacts-0-name': "John Lennon",
        'details-contacts-0-email': 'john@beatles.co.uk',
        'details-contacts-0-tel': ''
    }
    PERMISSIONS_POST_DATA = {
        'project_add_wizard-current_step': 'permissions',
        'permissions-org_member_1': 'PM',
        'permissions-org_member_2': 'DC',
        'permissions-org_member_3': 'PU',
        'permissions-org_member_4': 'Pb'
    }
    PERMISSIONS_POST_DATA_BAD = {
        'project_add_wizard-current_step': 'permissions',
        'permissions-org_member_1': 'PM',
        'permissions-org_member_2': 'DC',
        'permissions-org_member_3': 'PU',
        'permissions-org_member_4': 'Pb',
        'permissions-bad_user': 'PU'
    }
    DETAILS_POST_DATA_MANIPULATED = {
        'project_add_wizard-current_step': 'details',
        'details-organization': 'test-org',
        'details-name': 'Test Project FAKE',
        'details-description': 'This is a test project',
        'details-access': 'on',
        'details-url': 'http://www.test.org',
        'details-contacts-TOTAL_FORMS': 1,
        'details-contacts-INITIAL_FORMS': 0,
        'details-contacts-0-name': "John Lennon",
        'details-contacts-0-email': 'john@beatles.co.uk',
        'details-contacts-0-tel': ''
    }

    def test_full_flow_valid(self):
        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        self.DETAILS_POST_DATA['details-questionnaire'] = self.get_form(
            'xls-form')
        self.DETAILS_POST_DATA['details-original_file'] = 'original.xls'
        details_response = self.client.post(
            reverse('project:add'), self.DETAILS_POST_DATA
        )
        assert details_response.status_code == 200
        permissions_response = self.client.post(
            reverse('project:add'), self.PERMISSIONS_POST_DATA
        )
        assert permissions_response.status_code == 302
        assert ('/organizations/test-org/projects/test-project/' in
                permissions_response['location'])

        proj = Project.objects.get(organization=self.org, name='Test Project')
        assert proj.slug == 'test-project'
        assert proj.description == 'This is a test project'
        assert len(proj.contacts) == 1
        assert proj.contacts[0]['name'] == "John Lennon"
        assert proj.contacts[0]['email'] == 'john@beatles.co.uk'
        assert ProjectRole.objects.filter(project=proj).count() == 3
        for r in ProjectRole.objects.filter(project=proj):
            if r.user.username == 'org_member_1':
                assert r.role == 'PM'
            elif r.user.username == 'org_member_2':
                assert r.role == 'DC'
            elif r.user.username == 'org_member_3':
                assert r.role == 'PU'
            else:
                assert False

        questionnaire = Questionnaire.objects.get(project=proj)
        assert questionnaire.original_file == 'original.xls'

    def test_wizard_previous(self):
        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        post_data = self.DETAILS_POST_DATA.copy()
        post_data['wizard_goto_step'] = 'extents'
        details_response = self.client.post(
            reverse('project:add'), post_data
        )
        assert details_response.status_code == 200

    def test_flow_with_archived_organization(self):
        self.org.archived = True
        self.org.save()

        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        details_response = self.client.post(
            reverse('project:add'), self.DETAILS_POST_DATA
        )
        assert details_response.status_code == 200
        assert details_response.context_data['form'].is_valid() is False
        assert details_response.context_data['form'].errors == {
            'organization': ["Select a valid choice. test-org is "
                             "not one of the available choices."],
        }

    def test_full_flow_invalid_xlsform(self):
        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        details_post_data = self.DETAILS_POST_DATA.copy()
        details_post_data[
            'details-questionnaire'] = self.get_form(
            'xls-form-invalid')
        details_response = self.client.post(
            reverse('project:add'), details_post_data
        )
        assert details_response.status_code == 200
        permissions_response = self.client.post(
            reverse('project:add'), self.PERMISSIONS_POST_DATA
        )
        assert permissions_response.status_code == 200
        assert permissions_response.context_data['form'].is_valid() is False
        with pytest.raises(Project.DoesNotExist) as e:
            Project.objects.get(
                organization=self.org, slug='test-project')
            assert e.message == 'Project matching query does not exist.'

    def test_flow_with_org_is_chosen_function(self):
        second_org = OrganizationFactory.create(name="Second Org")
        OrganizationRole.objects.create(organization=second_org,
                                        user=self.users[0],
                                        admin=True)
        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        form = extents_response.context_data['form']
        assert len(form.fields['organization'].choices) == 3
        assert form.fields['organization'].choices[0] == (
            '', "Please select an organization")
        assert form.fields['organization'].choices[1][1] == "Second Org"
        assert form.fields['organization'].choices[2][1] == "Test Org"
        details_response = self.client.post(
            reverse('project:add'), self.DETAILS_POST_DATA
        )
        assert details_response.status_code == 200
        post_data = self.PERMISSIONS_POST_DATA.copy()
        post_data['wizard_goto_step'] = 'details'
        permissions_response = self.client.post(
            reverse('project:add'), post_data
        )
        assert permissions_response.status_code == 200
        form = permissions_response.context_data['form']
        assert len(form.fields['organization'].choices) == 2
        assert form.fields['organization'].choices[0][1] == "Second Org"
        assert form.fields['organization'].choices[1][1] == "Test Org"
        details_response = self.client.post(
            reverse('project:add'), self.DETAILS_POST_DATA
        )
        assert details_response.status_code == 200

    def test_full_flow_long_slug(self):
        project_name = (
            "Very Long Name For The Purposes of Testing That"
            " Slug Truncation Functions Correctly"
        )
        expected_slug = 'very-long-name-for-the-purposes-of-testing-that-sl'
        self.client.force_login(self.superuser)
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        details_post_data = self.DETAILS_POST_DATA.copy()
        details_post_data['details-name'] = project_name
        details_response = self.client.post(
            reverse('project:add'), details_post_data
        )
        assert details_response.status_code == 200
        permissions_response = self.client.post(
            reverse('project:add'), self.PERMISSIONS_POST_DATA
        )

        assert permissions_response.status_code == 302
        assert (
            '/organizations/test-org/projects/{}/'.format(expected_slug)
            in permissions_response['location']
        )

        proj = Project.objects.get(organization=self.org, slug=expected_slug)
        assert proj.slug == expected_slug
        assert proj.description == 'This is a test project'
        assert len(proj.contacts) == 1
        assert proj.contacts[0]['name'] == "John Lennon"
        assert proj.contacts[0]['email'] == 'john@beatles.co.uk'
        assert ProjectRole.objects.filter(project=proj).count() == 3
        for r in ProjectRole.objects.filter(project=proj):
            if r.user.username == 'org_member_1':
                assert r.role == 'PM'
            elif r.user.username == 'org_member_2':
                assert r.role == 'DC'
            elif r.user.username == 'org_member_3':
                assert r.role == 'PU'
            else:
                assert False

    def test_full_flow_with_organization_valid(self):
        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('organization:project-add',
                    kwargs={'organization': self.org.slug}),
            self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        self.DETAILS_POST_DATA['details-questionaire'] = self.get_form(
            'xls-form')
        details_response = self.client.post(
            reverse('organization:project-add',
                    kwargs={'organization': self.org.slug}),
            self.DETAILS_POST_DATA
        )
        assert details_response.status_code == 200
        permissions_response = self.client.post(
            reverse('organization:project-add',
                    kwargs={'organization': self.org.slug}),
            self.PERMISSIONS_POST_DATA
        )
        assert permissions_response.status_code == 302
        assert ('/organizations/test-org/projects/test-project/' in
                permissions_response['location'])

        proj = Project.objects.get(organization=self.org, name='Test Project')
        assert proj.slug == 'test-project'
        assert proj.description == 'This is a test project'
        assert len(proj.contacts) == 1
        assert proj.contacts[0]['name'] == "John Lennon"
        assert proj.contacts[0]['email'] == 'john@beatles.co.uk'
        assert ProjectRole.objects.filter(project=proj).count() == 3
        for r in ProjectRole.objects.filter(project=proj):
            if r.user.username == 'org_member_1':
                assert r.role == 'PM'
            elif r.user.username == 'org_member_2':
                assert r.role == 'DC'
            elif r.user.username == 'org_member_3':
                assert r.role == 'PU'
            else:
                assert False

        assert Questionnaire.objects.filter(project=proj).exists() is True


class ProjectEditGeometryTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectEditGeometry
    template = 'organization/project_edit_geometry.html'
    success_url_name = 'organization:project-dashboard'
    post_data = {
        'extent': '{"coordinates": [[[12.37, 51.36], '
                  '[12.35, 51.34], [12.36, 51.33], [12.4, 51.33], '
                  '[12.38, 51.35], [12.37, 51.36]]], "type": "Polygon"}'
    }

    def setup_models(self):
        self.project = ProjectFactory.create()

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_template_context(self):
        return {'project': self.project,
                'object': self.project,
                'form': forms.ProjectAddExtents(instance=self.project),
                'is_allowed_import': True}

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_archived_project(self):
        user = UserFactory.create()
        assign_policies(user)
        self.project.archived = True
        self.project.save()

        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user, method='POST')
        assert response.status_code == 302
        assert self.expected_success_url in response.location
        self.project.refresh_from_db()
        assert (json.loads(self.project.extent.json) ==
                json.loads(self.post_data.get('extent')))

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user, method='POST')
        assert response.status_code == 302

        assert ("You don't have permission to update this project"
                in response.messages)
        self.project.refresh_from_db()
        assert self.project.extent is None

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.project.refresh_from_db()
        assert self.project.extent is None

    def test_post_with_archived_project(self):
        user = UserFactory.create()
        assign_policies(user)
        self.project.archived = True
        self.project.save()
        response = self.request(user=user, method='POST')
        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)
        self.project.refresh_from_db()
        assert self.project.extent is None


@pytest.mark.usefixtures('make_dirs')
class ProjectEditDetailsTest(ViewTestCase, UserTestCase,
                             FileStorageTestCase, TestCase):
    view_class = default.ProjectEditDetails
    template = 'organization/project_edit_details.html'
    success_url_name = 'organization:project-dashboard'
    post_data = {
        'name': 'New Name',
        'description': 'New Description',
        'urls': '',
        'contacts-TOTAL_FORMS': 1,
        'contacts-INITIAL_FORMS': 0,
        'contacts-0-name': '',
        'contacts-0-email': '',
        'contacts-0-tel': ''
    }

    def setup_models(self):
        self.project = ProjectFactory.create(current_questionnaire='abc')
        self.questionnaire = q_factories.QuestionnaireFactory.create(
            project=self.project, id='abc')

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_template_context(self):
        return {'project': self.project,
                'object': self.project,
                'form': forms.ProjectEditDetails(
                    instance=self.project,
                    initial={'questionnaire': self.questionnaire.xls_form.url,
                             'original_file': self.questionnaire.original_file}
                ),
                'is_allowed_import': True}

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content
        assert 'Select the questionnaire' in self.expected_content

    def test_get_empty_questionnaire_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)

        self.project.current_questionnaire = ''
        self.project.save()

        form = forms.ProjectEditDetails(instance=self.project)

        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.render_content(form=form)
        assert 'Select the questionnaire' in self.expected_content

    def test_get_with_blocked_questionnaire_upload(self):
        user = UserFactory.create()
        assign_policies(user)
        SpatialUnitFactory.create(project=self.project)

        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content
        assert 'Select the questionnaire' not in self.expected_content

    def test_get_with_authorized_user_include_questionnaire(self):
        questionnaire = q_factories.QuestionnaireFactory.create(
            project=self.project)
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user)
        form = forms.ProjectEditDetails(
            instance=self.project,
            initial={'questionnaire': questionnaire.xls_form.url})
        assert response.status_code == 200
        assert response.content == self.render_content(form=form)

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_with_archived_project(self):
        self.project.archived = True
        self.project.save()
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user, method='POST',
                                post_data={'questionnaire': ''})

        assert response.status_code == 302
        assert self.expected_success_url in response.location
        self.project.refresh_from_db()
        assert self.project.name == self.post_data['name']
        assert self.project.description == self.post_data['description']
        assert self.project.current_questionnaire == ''

    def test_post_with_blocked_questionnaire_upload(self):
        SpatialUnitFactory.create(project=self.project)
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user, method='POST',
                                post_data={'questionnaire': ''})

        assert response.status_code == 200
        self.project.refresh_from_db()
        assert self.project.name != self.post_data['name']
        assert self.project.description != self.post_data['description']
        assert self.project.current_questionnaire == 'abc'

    def test_post_empty_questionnaire_with_blocked_questionnaire_upload(self):
        SpatialUnitFactory.create(project=self.project)
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user, method='POST')

        assert response.status_code == 302
        assert self.expected_success_url in response.location
        self.project.refresh_from_db()
        assert self.project.name == self.post_data['name']
        assert self.project.description == self.post_data['description']
        assert self.project.current_questionnaire == 'abc'

    def test_post_invalid_form(self):
        question = self.get_form('xls-form-invalid')
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user, method='POST',
                                post_data={'questionnaire': question})
        post_data = self.post_data.copy()
        post_data.update({'questionnaire': question})
        form = forms.ProjectEditDetails(
            instance=self.project,
            initial={'questionnaire': question},
            data=post_data
        )
        form.is_valid()
        form.add_error('questionnaire',
                       "Unknown question type 'interger'.")

        assert response.status_code == 200
        assert response.content == self.render_content(form=form)

    def test_update_missing_relevant(self):
        question = self.get_form('t_questionnaire_missing_relevant')
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user, method='POST',
                                post_data={'questionnaire': question})
        post_data = self.post_data.copy()
        post_data.update({'questionnaire': question})
        form = forms.ProjectEditDetails(
            instance=self.project,
            initial={'questionnaire': question},
            data=post_data
        )
        form.is_valid()
        form.add_error('questionnaire', MISSING_RELEVANT)

        assert response.status_code == 200
        assert response.content == self.render_content(form=form)

    def test_post_private_project_form(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user, method='POST',
                                post_data={'access': ['on']})

        assert response.status_code == 302
        self.project.refresh_from_db()
        assert self.project.access == 'private'

        response = self.request(user=user, method='POST',
                                post_data={})
        assert response.status_code == 302
        self.project.refresh_from_db()
        assert self.project.access == 'public'

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user, method='POST')

        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)
        self.project.refresh_from_db()
        assert self.project.name != self.post_data['name']
        assert self.project.description != self.post_data['description']

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.project.refresh_from_db()
        assert self.project.name != self.post_data['name']
        assert self.project.description != self.post_data['description']

    def test_post_with_archived_project(self):
        user = UserFactory.create()
        assign_policies(user)
        self.project.archived = True
        self.project.save()
        response = self.request(user=user, method='POST')

        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)
        self.project.refresh_from_db()
        assert self.project.name != self.post_data['name']
        assert self.project.description != self.post_data['description']


class ProjectEditPermissionsTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectEditPermissions
    template = 'organization/project_edit_permissions.html'
    success_url_name = 'organization:project-dashboard'

    def setup_models(self):
        self.project = ProjectFactory.create()

        self.project_user = UserFactory.create()
        OrganizationRole.objects.create(
            organization=self.project.organization,
            user=self.project_user
        )
        self.project_role = ProjectRole.objects.create(
            project=self.project,
            user=self.project_user,
            role='DC'
        )

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_post_data(self):
        return {self.project_user.username: 'PM'}

    def setup_template_context(self):
        return {'project': self.project,
                'object': self.project,
                'form': forms.ProjectEditPermissions(instance=self.project),
                'is_allowed_import': True}

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
        assert ("You don't have permission to update this project"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_get_with_archived_project(self):
        user = UserFactory.create()
        assign_policies(user)

        self.project.archived = True
        self.project.save()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this project"
                in response.messages)

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user, method='POST')

        assert self.expected_success_url in response.location
        self.project_role.refresh_from_db()
        assert self.project_role.role == 'PM'

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user, method='POST')
        assert response.status_code == 302

        assert ("You don't have permission to update this project"
                in response.messages)
        self.project_role.refresh_from_db()
        assert self.project_role.role == 'DC'

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location

        self.project_role.refresh_from_db()
        assert self.project_role.role == 'DC'

    def test_post_with_archived_project(self):
        user = UserFactory.create()
        assign_policies(user)
        self.project.archived = True
        self.project.save()
        response = self.request(user=user, method='POST')
        assert response.status_code == 302

        assert ("You don't have permission to update this project"
                in response.messages)
        self.project_role.refresh_from_db()
        assert self.project_role.role == 'DC'


class ProjectArchiveTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectArchive

    def setup_models(self):
        self.project = ProjectFactory.create()

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_archive_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)

        self.project.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/projects/{}/'.format(
            self.project.organization.slug, self.project.slug)
            in response.location)
        assert self.project.archived is True

    def test_archive_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)

        self.project.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to archive this project"
                in response.messages)
        assert self.project.archived is False

    def test_archive_with_unauthenticated_user(self):
        response = self.request()
        self.project.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.project.archived is False


class ProjectUnarchiveTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectUnarchive

    def setup_models(self):
        self.project = ProjectFactory.create(archived=True)

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_unarchive_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)

        self.project.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/projects/{}/'.format(
            self.project.organization.slug, self.project.slug)
            in response.location)
        assert self.project.archived is False

    def test_unarchive_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)

        self.project.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to unarchive this project"
                in response.messages)
        assert self.project.archived is True

    def test_unarchive_with_unauthenticated_user(self):
        response = self.request()
        self.project.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.project.archived is True

    def test_unarchive_with_archived_organization(self):
        user = UserFactory.create()
        assign_policies(user)

        self.project.refresh_from_db()
        self.project.organization.archived = True
        self.project.organization.save()

        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to unarchive this project"
                in response.messages)
        self.project.refresh_from_db()
        assert self.project.archived is True


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class ProjectDataDownloadTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectDataDownload
    post_data = {'type': 'xls', 'include_resources': False}
    template = 'organization/project_download.html'

    def setup_models(self):
        ensure_dirs()
        self.project = ProjectFactory.create()
        geometry = 'SRID=4326;POINT (30 10)'
        SpatialUnitFactory.create(project=self.project, geometry=geometry)
        self.user = UserFactory.create()

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def setup_template_context(self):
        return {'project': self.project,
                'object': self.project,
                'form': forms.DownloadForm(project=self.project,
                                           user=self.user),
                'is_allowed_import': True}

    def test_get_with_authorized_user(self):
        assign_policies(self.user)

        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert ("You don't have permission to export data from this project"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        assign_policies(self.user)
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 200
        assert (response.headers['content-disposition'][1] ==
                'attachment; filename={}.xlsx'.format(self.project.slug))
        assert (response.headers['content-type'][1] ==
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet')

    def test_post_with_unauthorized_user(self):
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 302
        assert ("You don't have permission to export data from this project"
                in response.messages)

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location


@pytest.mark.usefixtures('make_dirs')
@pytest.mark.usefixtures('clear_temp')
class ProjectDataImportTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        super().setUp()
        self.view = default.ProjectDataImportWizard.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*']),
                clause('allow', ['project.import'], ['project/*/*']),
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.user = UserFactory.create()
        self.unauth_user = UserFactory.create()

        setattr(self.request, 'user', self.user)
        assign_user_policies(self.user, self.policy)

        self.org = OrganizationFactory.create(
            name='Test Org', slug='test-org'
        )

        self.valid_csv = '/organization/tests/files/test.csv'
        self.valid_csv_custom = '/organization/tests/files/test_custom.csv'
        self.invalid_csv = '/organization/tests/files/test_invalid.csv'
        self.geoshape_csv = '/organization/tests/files/test_geoshape.csv'
        self.geotrace_csv = '/organization/tests/files/test_geotrace.csv'
        self.invalid_file_type = '/organization/tests/files/test_invalid.kml'
        self.valid_xls = '/organization/tests/files/test_download.xlsx'

        self.project = ProjectFactory.create(
            name='Test Imports',
            slug='test-imports', organization=self.org)
        xlscontent = self.get_file(
            '/organization/tests/files/uttaran_test.xlsx', 'rb'
        )
        form = self.storage.save('xls-forms/uttaran_test.xlsx',
                                 xlscontent.read())
        xlscontent.close()

        Questionnaire.objects.create_from_form(
            xls_form=form,
            project=self.project
        )
        # test for expected schema and attribute creation
        assert 3 == Schema.objects.all().count()
        assert 42 == Attribute.objects.all().count()

        self.party_attributes = [
            'party::educational_qualification', 'party::name_mouza',
            'party::j_l', 'party::name_father_hus', 'party::village_name',
            'party::mobile_no', 'party::occupation_hh', 'party::class_hh'
        ]
        self.location_attributes = [
            'spatialunit::deed_of_land', 'spatialunit::amount_othersland',
            'spatialunit::land_calculation', 'spatialunit::how_aquire_landwh',
            'spatialunit::female_member', 'spaitalunit::mutation_of_land',
            'spatialunit::amount_agriland', 'spatialunit::nid_number',
            'spatialunit::how_aquire_landt', 'spatialunit::boundary_conflict',
            'spatialunit::dakhal_on_land', 'spatialunit::how_aquire_landp',
            'spatialunit::how_aquire_landd', 'spatialunit::ownership_conflict',
            'spatialunit::others_conflict', 'spatialunit::how_aquire_landm',
            'spatialunit::khatain_of_land', 'spatialunit::male_member',
            'spatialunit::how_aquire_landw', 'spatialunit::everything',
            'spatialunit::location_problems'
        ]
        self.tenure_attributes = [
            'tenurerelationship::tenure_name',
            'tenurerelationship::tenure_notes'
        ]

        self.ATTRIBUTES = (
            self.party_attributes + self.location_attributes +
            self.tenure_attributes
        )
        self.EXTRA_ATTRS = [
            'conflicts_resolution', 'current_address', 'data_collector_name',
            'gender', 'howconflict_resolution', 'land_amount', 'land_class',
            'legal_support', 'legal_support_details', 'marital_status',
            'multiple_landowners'
        ]
        self.EXTRA_HEADERS = [
            'audio_hh', 'conflicts_resoulation', 'location_geometry',
            'geo_type', 'howconflict_resoulation', 'image_hh', 'name_of_hh',
            'phonenumber', 'present_add'
        ]
        self.SELECT_FILE_POST_DATA = {
            'project_data_import_wizard-current_step': 'select_file',
            'select_file-name': 'Test Imports',
            'select_file-description': 'A description of the import',
            'select_file-type': 'csv',
            'select_file-entity_types': ['PT', 'SU']
        }
        self.MAP_ATTRIBUTES_POST_DATA = {
            'project_data_import_wizard-current_step': 'map_attributes',
            'attributes': self.ATTRIBUTES,
            'extra_attrs': self.EXTRA_ATTRS,
            'extra_headers': self.EXTRA_HEADERS
        }
        self.SELECT_DEFAULTS_POST_DATA = {
            'project_data_import_wizard-current_step': 'select_defaults',
            'select_defaults-party_name_field': 'name_of_hh',
            'select_defaults-file': (settings.MEDIA_ROOT +
                                     '/temp/test.csv'),
            'select_defaults-party_type_field': 'party_type',
            'select_defaults-geometry_field': 'location_geometry',
            'select_defaults-location_type_field': 'location_type'
        }

    def _get(self, status=None, check_content=False, login_redirect=False):
        response = self.client.get(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug})
        )
        if status is not None:
            assert response.status_code == status
        if login_redirect:
            assert '/account/login/' in response['location']
        if check_content:
            content = response.content.decode('utf-8')
            expected = render_to_string(
                'organization/project_select_import.html',
                context=response.context_data,
                request=response.wsgi_request
            )
            assert remove_csrf(expected) == remove_csrf(content)

    def test_initial_get_valid(self):
        self.client.force_login(self.user)
        self._get(status=200, check_content=True)

    def test_initial_get_with_unauthorized_user(self):
        self.client.force_login(self.unauth_user)
        self._get(status=302, check_content=False)

    def test_initial_get_with_unauthenticated_user(self):
        self._get(status=302, login_redirect=True)

    def test_full_flow_valid(self):
        self.client.force_login(self.user)
        csvfile = self.get_file(self.valid_csv, 'rb')
        file = SimpleUploadedFile('test.csv', csvfile.read(), 'text/csv')
        csvfile.close()
        post_data = self.SELECT_FILE_POST_DATA.copy()
        post_data['select_file-file'] = file
        post_data['select_file-is_resource'] = True
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        map_attributes_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.MAP_ATTRIBUTES_POST_DATA
        )
        assert map_attributes_response.status_code == 200

        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.SELECT_DEFAULTS_POST_DATA
        )
        assert select_defaults_response.status_code == 302

        assert ('/organizations/test-org/projects/test-imports/' in
                select_defaults_response['location'])

        proj = Project.objects.get(
            organization=self.org, name='Test Imports')
        assert Party.objects.filter(project_id=proj.pk).count() == 10
        assert SpatialUnit.objects.filter(project_id=proj.pk).count() == 10
        assert Resource.objects.filter(project_id=proj.pk).count() == 1
        assert TenureRelationship.objects.filter(
            project_id=proj.pk).count() == 10

        for su in SpatialUnit.objects.filter(project_id=proj.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test resource creation
        resource = Resource.objects.filter(project_id=proj.pk).first()
        assert resource.original_file == 'test.csv'
        assert resource.mime_type == 'text/csv'
        random_filename = resource.file.url[resource.file.url.rfind('/'):]
        assert random_filename.endswith('.csv')
        assert len(random_filename.split('.')[0].strip('/')) == 24

    def test_full_flow_valid_custom_types(self):
        questionnaire = q_factories.QuestionnaireFactory.create(
            project=self.project)
        question = q_factories.QuestionFactory.create(
            type='S1',
            name='tenure_type',
            questionnaire=questionnaire)
        q_factories.QuestionOptionFactory.create(
            question=question,
            name='AA',
            label='AA Label')
        question = q_factories.QuestionFactory.create(
            type='S1',
            name='location_type',
            questionnaire=questionnaire)
        q_factories.QuestionOptionFactory.create(
            question=question,
            name='BB',
            label='BB Label')

        self.client.force_login(self.user)
        csvfile = self.get_file(self.valid_csv_custom, 'rb')
        file = SimpleUploadedFile('test_custom.csv', csvfile.read(),
                                  'text/csv')
        csvfile.close()
        post_data = self.SELECT_FILE_POST_DATA.copy()
        post_data['select_file-file'] = file
        post_data['select_file-is_resource'] = True
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        map_attributes_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.MAP_ATTRIBUTES_POST_DATA
        )
        assert map_attributes_response.status_code == 200

        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.SELECT_DEFAULTS_POST_DATA
        )
        assert select_defaults_response.status_code == 302

        assert ('/organizations/test-org/projects/test-imports/' in
                select_defaults_response['location'])

        proj = Project.objects.get(
            organization=self.org, name='Test Imports')
        assert Party.objects.filter(project_id=proj.pk).count() == 10
        assert SpatialUnit.objects.filter(project_id=proj.pk).count() == 10
        assert Resource.objects.filter(project_id=proj.pk).count() == 1
        assert TenureRelationship.objects.filter(
            project_id=proj.pk).count() == 10

        for su in SpatialUnit.objects.filter(project_id=proj.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test resource creation
        resource = Resource.objects.filter(project_id=proj.pk).first()
        assert resource.original_file == 'test_custom.csv'
        assert resource.mime_type == 'text/csv'
        random_filename = resource.file.url[resource.file.url.rfind('/'):]
        assert random_filename.endswith('.csv')
        assert len(random_filename.split('.')[0].strip('/')) == 24

    def test_full_flow_valid_xls(self):
        mime = 'application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet'
        self.client.force_login(self.user)
        xlsfile = self.get_file(self.valid_xls, 'rb')
        file = SimpleUploadedFile('test_download.xlsx', xlsfile.read(), mime)
        xlsfile.close()
        post_data = self.SELECT_FILE_POST_DATA.copy()
        post_data['select_file-file'] = file
        post_data['select_file-is_resource'] = True
        post_data['select_file-type'] = 'xls'
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        map_attributes_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.MAP_ATTRIBUTES_POST_DATA
        )
        assert map_attributes_response.status_code == 200
        defaults_post_data = self.SELECT_DEFAULTS_POST_DATA.copy()
        defaults_post_data['select_defaults-file'] = (
            settings.MEDIA_ROOT + '/temp/test_download.xlsx'
        )
        defaults_post_data['select_defaults-party_name_field'] = 'name'
        defaults_post_data['select_defaults-party_type_field'] = 'type'
        defaults_post_data[
            'select_defaults-geometry_field'] = 'geometry.ewkt'
        defaults_post_data[
            'select_defaults-location_type_field'] = 'type'
        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            defaults_post_data
        )
        assert select_defaults_response.status_code == 302

        assert ('/organizations/test-org/projects/test-imports/' in
                select_defaults_response['location'])

        proj = Project.objects.get(
            organization=self.org, name='Test Imports')
        assert Party.objects.filter(project_id=proj.pk).count() == 10
        assert SpatialUnit.objects.filter(project_id=proj.pk).count() == 10
        assert Resource.objects.filter(project_id=proj.pk).count() == 1
        assert TenureRelationship.objects.filter(
            project_id=proj.pk).count() == 10

        for su in SpatialUnit.objects.filter(project_id=proj.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        resource = Resource.objects.filter(project_id=proj.pk).first()
        assert resource.original_file == 'test_download.xlsx'

    def test_full_flow_invalid_value(self):
        self.client.force_login(self.user)
        csvfile = self.get_file(self.invalid_csv, 'rb')
        file = SimpleUploadedFile('test_invalid.csv', csvfile.read(),
                                  'text/csv')
        csvfile.close()
        post_data = self.SELECT_FILE_POST_DATA.copy()
        post_data['select_file-file'] = file
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        map_attributes_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.MAP_ATTRIBUTES_POST_DATA
        )
        assert map_attributes_response.status_code == 200

        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.SELECT_DEFAULTS_POST_DATA
        )
        assert select_defaults_response.status_code == 200

        proj = Project.objects.get(
            organization=self.org, name='Test Imports')
        assert Party.objects.filter(project_id=proj.pk).count() == 0
        assert SpatialUnit.objects.filter(project_id=proj.pk).count() == 0
        assert TenureRelationship.objects.filter(
            project_id=proj.pk).count() == 0

    def test_full_flow_invalid_file_type(self):
        self.client.force_login(self.user)
        invalid_file = self.get_file(self.invalid_file_type, 'rb')
        file = SimpleUploadedFile(
            'test_invalid.kml', invalid_file.read(), 'application/kml')
        invalid_file.close()
        post_data = self.SELECT_FILE_POST_DATA.copy()
        post_data['select_file-file'] = file
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        map_attributes_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.MAP_ATTRIBUTES_POST_DATA
        )
        assert map_attributes_response.status_code == 200

        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.SELECT_DEFAULTS_POST_DATA
        )
        assert select_defaults_response.status_code == 200

        proj = Project.objects.get(
            organization=self.org, name='Test Imports')
        assert Party.objects.filter(project_id=proj.pk).count() == 0
        assert SpatialUnit.objects.filter(project_id=proj.pk).count() == 0
        assert TenureRelationship.objects.filter(
            project_id=proj.pk).count() == 0

    def test_wizard_goto_step(self):
        self.client.force_login(self.user)

        # post first page data
        csvfile = self.get_file(self.valid_csv, 'rb')
        file = SimpleUploadedFile('test.csv', csvfile.read(), 'text/csv')
        csvfile.close()
        post_data = self.SELECT_FILE_POST_DATA.copy()
        post_data['select_file-file'] = file
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        # test file upload saved to disk
        assert os.path.exists(settings.MEDIA_ROOT + '/temp/test.csv')

        # go to select defaults page
        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.MAP_ATTRIBUTES_POST_DATA
        )
        assert select_defaults_response.status_code == 200

        # return to map attributes page
        post_data = self.SELECT_DEFAULTS_POST_DATA.copy()
        post_data['wizard_goto_step'] = 'map_attributes'
        map_attributes_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert map_attributes_response.status_code == 200

        # return to first page
        post_data = {}
        post_data['wizard_goto_step'] = 'select_file'
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        # test for uploaded file removal when navigating back to first page
        assert not os.path.exists(settings.MEDIA_ROOT + '/temp/test.csv')

        # test goto select_defaults
        post_data = self.SELECT_DEFAULTS_POST_DATA.copy()
        post_data['wizard_goto_step'] = 'select_defaults'
        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_defaults_response.status_code == 200

    def test_full_flow_valid_no_resource(self):
        self.client.force_login(self.user)
        csvfile = self.get_file(self.valid_csv, 'rb')
        file = SimpleUploadedFile('test.csv', csvfile.read(), 'text/csv')
        csvfile.close()
        post_data = self.SELECT_FILE_POST_DATA.copy()
        post_data['select_file-file'] = file
        post_data['select_file-is_resource'] = False
        select_file_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            post_data
        )
        assert select_file_response.status_code == 200

        map_attributes_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.MAP_ATTRIBUTES_POST_DATA
        )
        assert map_attributes_response.status_code == 200

        select_defaults_response = self.client.post(
            reverse('organization:project-import',
                    kwargs={
                        'organization': self.org.slug,
                        'project': self.project.slug}),
            self.SELECT_DEFAULTS_POST_DATA
        )
        assert select_defaults_response.status_code == 302

        assert ('/organizations/test-org/projects/test-imports/' in
                select_defaults_response['location'])

        proj = Project.objects.get(
            organization=self.org, name='Test Imports')
        assert Party.objects.filter(project_id=proj.pk).count() == 10
        assert SpatialUnit.objects.filter(project_id=proj.pk).count() == 10
        assert Resource.objects.filter(project_id=proj.pk).count() == 0
        assert TenureRelationship.objects.filter(
            project_id=proj.pk).count() == 10

        for su in SpatialUnit.objects.filter(project_id=proj.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point
