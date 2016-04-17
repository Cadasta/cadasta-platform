import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http import HttpRequest, Http404
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages.api import get_messages
import pytest

from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from organization.models import OrganizationRole, Project, ProjectRole
from ..views import default
from .factories import OrganizationFactory, ProjectFactory, clause


class ProjectListTest(TestCase):
    def setUp(self):
        self.view = default.ProjectList.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.ok_org1 = OrganizationFactory.create(
            name='OK org 1', slug='org1'
        )
        self.ok_org2 = OrganizationFactory.create(
            name='OK org 2', slug='org2'
        )
        self.unath_org = OrganizationFactory.create(
            name='Unauthorized org', slug='unauth-org'
        )
        self.projs = []
        self.projs += ProjectFactory.create_batch(2, organization=self.ok_org1)
        self.projs += ProjectFactory.create_batch(2, organization=self.ok_org2)
        ProjectFactory.create(
            name='Unauthorized project',
            project_slug='unauth-proj',
            organization=self.ok_org2
        )
        ProjectFactory.create(
            name='Project in unauthorized org',
            project_slug='proj-in-unath-org',
            organization=self.unath_org
        )

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

    def test_get_with_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        response = self.view(self.request).render()
        content = response.content.decode('utf-8')

        expected = render_to_string(
            'organization/project_list.html',
            {'object_list': self.projs,
             'add_allowed': True,
             'user': self.request.user},
            request=self.request)

        assert response.status_code == 200
        assert expected == content


class ProjectDashboardTest(TestCase):
    def setUp(self):
        self.view = default.ProjectDashboard.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        self.project1 = ProjectFactory.create()
        self.project2 = ProjectFactory.create(
            extent=('SRID=4326;'
                    'POLYGON ((-5.1031494140625000 8.1299292850467957, '
                    '-5.0482177734375000 7.6837733211111425, '
                    '-4.6746826171875000 7.8252894725496338, '
                    '-4.8641967773437491 8.2278005261522775, '
                    '-5.1031494140625000 8.1299292850467957))')
        )

        clauses = {
            'clause': [
                clause('allow', ['project.list']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.user = UserFactory.create()
        setattr(self.request, 'user', self.user)

    def _get(self, project, status=None):
        response = self.view(self.request,
                             organization=project.organization.slug,
                             project=project.project_slug)
        if status is not None:
            assert response.status_code == status
        return response

    def test_get_with_authorized_user(self):
        assign_user_policies(self.user, self.policy)
        response = self._get(self.project1, status=200).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['object'] = self.project1
        context['project'] = self.project1
        expected = render_to_string(
            'organization/project_dashboard.html',
            context, request=self.request
        )

        assert expected == content

    def test_get_with_unauthorized_user(self):
        self._get(self.project1, status=302)
        assert ("You don't have permission to access this project"
                in [str(m) for m in get_messages(self.request)])

    def test_get_non_existent_project(self):
        assign_user_policies(self.user, self.policy)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org', project='some-project')

    def test_get_with_project_extent(self):
        assign_user_policies(self.user, self.policy)
        response = self._get(self.project2, status=200).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['object'] = self.project2
        context['project'] = self.project2
        default.assign_project_extent_context(context, self.project2)
        expected = render_to_string(
            'organization/project_dashboard.html',
            context, request=self.request
        )

        assert expected == content


class ProjectAddTest(TestCase):
    def setUp(self):
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
            {'username': 'org_non_member_1'},
            {'username': 'org_non_member_2'},
            {'username': 'org_non_member_3'},
            {'username': 'org_non_member_4'}])
        for idx in range(5):
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
            assert expected == content

    def test_initial_get_valid(self):
        self.client.force_login(self.user)
        self._get(status=200, check_content=True)

    def test_initial_get_with_unauthorized_user(self):
        self.client.force_login(self.unauth_user)
        self._get(status=200, check_content=True)

    def test_initial_get_with_unauthenticated_user(self):
        self._get(status=302, login_redirect=True)

    EXTENTS_POST_DATA = {
        'project_add_wizard-current_step': 'extents',
        'extents-location':
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
        'details-public': 'true',
        'details-url': 'http://www.test.org'
    }
    PERMISSIONS_POST_DATA = {
        'project_add_wizard-current_step': 'permissions',
        'org_member_1': 'PM',
        'org_member_2': 'DC',
        'org_member_3': 'PU'
    }
    PERMISSIONS_POST_DATA_BAD = {
        'project_add_wizard-current_step': 'permissions',
        'org_member_1': 'PM',
        'org_member_2': 'DC',
        'org_member_3': 'PU',
        'bad_user': 'PU'
    }

    def test_full_flow_valid(self):
        self.client.force_login(self.user)
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
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
        assert proj.project_slug == 'test-project'
        assert proj.description == 'This is a test project'
        for r in ProjectRole.objects.filter(project=proj):
            if r.user.username == 'org_member_1':
                assert r.role == 'PM'
            elif r.user.username == 'org_member_2':
                assert r.role == 'DC'
            elif r.user.username == 'org_member_3':
                assert r.role == 'PU'
            else:
                assert False
        # assert proj.public
