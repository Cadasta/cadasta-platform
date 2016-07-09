import os
import os.path
import json
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpRequest, Http404
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages.api import get_messages
import pytest

from tutelary.models import Policy, Role, assign_user_policies
from buckets.test.utils import ensure_dirs
from buckets.test.storage import FakeS3Storage

from core.tests.base_test_case import UserTestCase
from core.tests.factories import RoleFactory
from accounts.tests.factories import UserFactory
from organization.models import OrganizationRole, Project, ProjectRole
from questionnaires.tests.factories import QuestionnaireFactory
from questionnaires.models import Questionnaire
from ..views import default
from .. import forms
from .factories import OrganizationFactory, ProjectFactory, clause


class ProjectListTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.ProjectList.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

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

    def _get(self, user=None, status=None, projs=None,
             make_org_member=None, is_superuser=False):
        if user is None:
            user = self.user
        if projs is None:
            projs = self.projs
        if make_org_member is not None:
            for org in make_org_member:
                OrganizationRole.objects.create(organization=org, user=user)
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        if status is not None:
            assert response.status_code == status
        content = response.render().content.decode('utf-8')

        expected = render_to_string(
            'organization/project_list.html',
            {'object_list':
             sorted(projs,
                    key=lambda p: p.organization.slug + ':' + p.slug),
             'add_allowed': True,
             'user': self.request.user,
             'is_superuser': is_superuser},
            request=self.request)

        if expected != content:
            with open('expected.txt', 'w') as fp:
                print(expected, file=fp)
            with open('content.txt', 'w') as fp:
                print(content, file=fp)
        assert expected == content

    def test_get_with_valid_user(self):
        self._get(status=200, projs=self.projs+self.unauth_projs)

    def test_get_with_unauthenticated_user(self):
        self._get(status=200, user=AnonymousUser(),
                  projs=self.projs + self.unauth_projs)

    def test_get_with_unauthorized_user(self):
        # Slight weirdness here: an unauthorized user can see *more*
        # projects than a user authorized with the policy defined
        # above because the policy includes clauses denying access to
        # some projects.
        self._get(status=200, user=UserFactory.create(),
                  projs=self.projs+self.unauth_projs)

    def test_get_with_org_membership(self):
        self._get(status=200, make_org_member=[self.ok_org1],
                  projs=(self.projs + self.unauth_projs +
                         [self.priv_proj1, self.priv_proj2]))

    def test_get_with_org_memberships(self):
        self._get(status=200, make_org_member=[self.ok_org1, self.ok_org2],
                  projs=self.projs + self.unauth_projs + [
                      self.priv_proj1, self.priv_proj2, self.priv_proj3
                  ])

    def test_get_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)
        self._get(status=200, user=superuser, is_superuser=True,
                  projs=Project.objects.all())


class ProjectDashboardTest(UserTestCase):
    def setUp(self):
        super().setUp()
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

        self.user = UserFactory.create()
        self.user.assign_policies(self.policy)
        self.restricted_user = UserFactory.create()
        self.restricted_user.assign_policies(restricted_policy)

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def _get(self, project, user=None, status=None):
        if user is None:
            user = self.user
        setattr(self.request, 'user', user)
        response = self.view(self.request,
                             organization=project.organization.slug,
                             project=project.slug)
        if status is not None:
            assert response.status_code == status
        return response

    def _get_private(self, status=None, user=None, make_org_member=False,
                     make_other_org_member=False, remove_org_member=False):
        if user is None:
            user = self.user
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='project', organization=org,
            name='Test Project', access='private'
        )
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if remove_org_member:
            OrganizationRole.objects.filter(
                organization=org, user=user
            ).delete()
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        return self._get(prj, user=user, status=status), prj

    def _check_render(self, response, project, assign_context=False):
        content = response.render().content.decode('utf-8')

        context = RequestContext(self.request)
        context['object'] = project
        context['project'] = project
        if assign_context:
            default.assign_project_extent_context(context, project)
        expected = render_to_string(
            'organization/project_dashboard.html',
            context, request=self.request
        )

        assert expected == content

    def _check_fail(self):
        assert ("You don't have permission to access this project"
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_authorized_user(self):
        response = self._get(self.project1, status=200)
        self._check_render(response, self.project1)

    def test_get_with_unauthorized_user(self):
        response = self._get(self.project1, user=UserFactory.create(),
                             status=200)
        self._check_render(response, self.project1)

    def test_get_with_superuser(self):
        superuser = UserFactory.create()
        superuser_pol = Policy.objects.get(name='superuser')
        self.superuser_role = RoleFactory.create(
            name='superuser', policies=[superuser_pol]
        )
        superuser.assign_policies(self.superuser_role)
        response = self._get(self.project1, user=superuser, status=200)
        self._check_render(response, self.project1,)

    def test_get_non_existent_project(self):
        setattr(self.request, 'user', self.user)
        with pytest.raises(Http404):
            self.view(self.request,
                      organization='some-org', project='some-project')

    def test_get_with_project_extent(self):
        response = self._get(self.project2, status=200)
        self._check_render(response, self.project2, assign_context=True)

    def test_get_private_project(self):
        response, prj = self._get_private(status=200)
        self._check_render(response, prj)

    def test_get_private_project_with_unauthenticated_user(self):
        self._get_private(user=AnonymousUser(), status=302)
        self._check_fail()

    def test_get_private_project_without_permission(self):
        self._get_private(user=self.restricted_user, status=302)
        self._check_fail()

    def test_get_private_project_based_on_org_membership(self):
        response, prj = self._get_private(
            user=UserFactory.create(), status=200, make_org_member=True
        )
        self._check_render(response, prj)

    def test_get_private_project_with_other_org_membership(self):
        self._get_private(
            user=UserFactory.create(), status=302,
            make_other_org_member=True
        )
        self._check_fail()

    def test_get_private_project_on_org_membership_removal(self):
        self._get_private(
            user=UserFactory.create(), status=302,
            make_org_member=True, remove_org_member=True
        )
        self._check_fail()

    def test_get_private_project_with_superuser(self):
        superuser = UserFactory.create()
        superuser_pol = Policy.objects.get(name='superuser')
        self.superuser_role = RoleFactory.create(
            name='superuser', policies=[superuser_pol]
        )
        superuser.assign_policies(self.superuser_role)
        response, prj = self._get_private(
            user=superuser, status=200
        )
        self._check_render(response, prj)


class ProjectAddTest(UserTestCase):
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

    def test_get_from_initial_with_no_org(self):
        """ If a project is created from scratch, no the initial value for
            `organization must be empty.
        """
        view = default.ProjectAddWizard()
        setattr(view, 'initial_dict', {'details': {}})
        setattr(view, 'kwargs', {})
        form_initial = view.get_form_initial('details')

        assert 'organization' not in form_initial

    def _get_xls_form(self, form_name):
        ensure_dirs(add='s3/uploads/xls-forms')

        path = os.path.dirname(settings.BASE_DIR)
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb').read()
        form = storage.save('xls-forms/' + form_name + '.xlsx', file)
        return form

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
        'details-contacts-0-name': '',
        'details-contacts-0-email': '',
        'details-contacts-0-tel': ''
    }
    PERMISSIONS_POST_DATA = {
        'project_add_wizard-current_step': 'permissions',
        'permissions-org_member_1': 'PM',
        'permissions-org_member_2': 'DC',
        'permissions-org_member_3': 'PU'
    }
    PERMISSIONS_POST_DATA_BAD = {
        'project_add_wizard-current_step': 'permissions',
        'permissions-org_member_1': 'PM',
        'permissions-org_member_2': 'DC',
        'permissions-org_member_3': 'PU',
        'permissions-bad_user': 'PU'
    }

    def test_full_flow_valid(self):
        self.client.force_login(self.user)
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        self.DETAILS_POST_DATA['details-questionaire'] = self._get_xls_form(
            'xls-form')
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
        # assert proj.public

    def test_full_flow_invalid_xlsform(self):
        self.client.force_login(self.user)
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        self.DETAILS_POST_DATA['details-questionaire'] = self._get_xls_form(
            'xls-form-invalid')
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
        for r in ProjectRole.objects.filter(project=proj):
            if r.user.username == 'org_member_1':
                assert r.role == 'PM'
            elif r.user.username == 'org_member_2':
                assert r.role == 'DC'
            elif r.user.username == 'org_member_3':
                assert r.role == 'PU'
            else:
                assert False

        assert Questionnaire.objects.filter(project=proj).exists() is False


class ProjectEditGeometryTest(UserTestCase):
    post_data = {
        'extent': '{"coordinates": [[[12.37, 51.36], '
                  '[12.35, 51.34], [12.36, 51.33], [12.4, 51.33], '
                  '[12.38, 51.35], [12.37, 51.36]]], "type": "Polygon"}'
    }

    def setUp(self):
        super().setUp()
        self.view = default.ProjectEditGeometry.as_view()
        self.request = HttpRequest()

        self.project = ProjectFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['project.update'], ['project/*/*']),
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

    def req(self, method='GET', user=AnonymousUser(), status=None):
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', method)

        if method == 'POST':
            setattr(self.request, 'POST', self.post_data)

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)
        if status:
            assert response.status_code == status

        if response.status_code == 200:
            response = response.render()

        return response

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)

        response = self.req(user=user, status=200)
        content = response.content.decode('utf-8')

        expected = render_to_string(
            'organization/project_edit_geometry.html',
            {'project': self.project,
             'object': self.project,
             'form': forms.ProjectAddExtents(instance=self.project)},
            request=self.request)

        assert expected == content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, status=302)
        assert ("You don't have permission to update this project"
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.req(status=302)
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        response = self.req(user=user, method='POST', status=302)

        expected_redirect = reverse(
            'organization:project-dashboard',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
            }
        )
        assert expected_redirect in response['location']
        self.project.refresh_from_db()
        assert (json.loads(self.project.extent.json) ==
                json.loads(self.post_data.get('extent')))

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, method='POST', status=302)

        assert ("You don't have permission to update this project"
                in [str(m) for m in get_messages(self.request)])
        self.project.refresh_from_db()
        assert self.project.extent is None

    def test_post_with_unauthenticated_user(self):
        response = self.req(method='POST', status=302)
        assert '/account/login/' in response['location']

        self.project.refresh_from_db()
        assert self.project.extent is None


class ProjectEditDetailsTest(UserTestCase):
    post_data = {
        'name': 'New Name',
        'description': 'New Description',
        'access': 'public',
        'urls': '',
        'questionnaire': '',
        'contacts-TOTAL_FORMS': 1,
        'contacts-INITIAL_FORMS': 0,
        'contacts-0-name': '',
        'contacts-0-email': '',
        'contacts-0-tel': ''
    }

    def setUp(self):
        super().setUp()
        self.view = default.ProjectEditDetails.as_view()
        self.request = HttpRequest()

        self.project = ProjectFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['project.update'], ['project/*/*']),
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

    def req(self, method='GET', user=AnonymousUser(), status=None):
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', method)

        if method == 'POST':
            setattr(self.request, 'POST', self.post_data)

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)
        if status:
            assert response.status_code == status

        if response.status_code == 200:
            response = response.render()

        return response

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)

        response = self.req(user=user, status=200)
        content = response.content.decode('utf-8')

        expected = render_to_string(
            'organization/project_edit_details.html',
            {'project': self.project,
             'object': self.project,
             'form': forms.ProjectEditDetails(
                instance=self.project)},
            request=self.request)

        assert expected == content

    def test_get_with_authorized_user_include_questionnaire(self):
        questionnaire = QuestionnaireFactory.create(project=self.project)
        user = UserFactory.create()
        assign_user_policies(user, self.policy)

        response = self.req(user=user, status=200)
        content = response.content.decode('utf-8')

        expected = render_to_string(
            'organization/project_edit_details.html',
            {'project': self.project,
             'object': self.project,
             'form': forms.ProjectEditDetails(
                instance=self.project,
                initial={'questionnaire': questionnaire.xls_form.url})},
            request=self.request)

        assert expected == content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, status=302)
        assert ("You don't have permission to update this project"
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.req(status=302)
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        response = self.req(user=user, method='POST', status=302)

        expected_redirect = reverse(
            'organization:project-dashboard',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
            }
        )
        assert expected_redirect in response['location']
        self.project.refresh_from_db()
        assert self.project.name == self.post_data['name']
        assert self.project.description == self.post_data['description']

    def test_post_invalid_form(self):
        path = os.path.dirname(settings.BASE_DIR)
        ensure_dirs()

        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/xls-form-invalid.xlsx',
            'rb'
        ).read()
        questionnaire = storage.save('xls-forms/xls-form-invalid.xlsx', file)
        self.post_data['questionnaire'] = questionnaire

        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        response = self.req(user=user, method='POST', status=200)
        content = response.content.decode('utf-8')

        form = forms.ProjectEditDetails(
                instance=self.project,
                initial={'questionnaire': questionnaire},
                data=self.post_data)

        form.add_error('questionnaire',
                       "'interger' is not an accepted question type")
        form.add_error('questionnaire',
                       "'select multiple list' is not an accepted question "
                       "type")

        expected = render_to_string(
            'organization/project_edit_details.html',
            {'project': self.project,
             'object': self.project,
             'form': form},
            request=self.request)

        assert expected == content
        self.post_data['questionnaire'] = ''

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, method='POST', status=302)

        assert ("You don't have permission to update this project"
                in [str(m) for m in get_messages(self.request)])
        self.project.refresh_from_db()
        assert self.project.name != self.post_data['name']
        assert self.project.description != self.post_data['description']

    def test_post_with_unauthenticated_user(self):
        response = self.req(method='POST', status=302)
        assert '/account/login/' in response['location']

        self.project.refresh_from_db()
        assert self.project.name != self.post_data['name']
        assert self.project.description != self.post_data['description']


class ProjectEditPermissionsTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.ProjectEditPermissions.as_view()
        self.request = HttpRequest()

        self.project = ProjectFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['project.update'], ['project/*/*']),
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

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

        self.post_data = {
            self.project_user.username: 'PM'
        }

    def req(self, method='GET', user=AnonymousUser(), status=None):
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', method)

        if method == 'POST':
            setattr(self.request, 'POST', self.post_data)

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)
        if status:
            assert response.status_code == status

        if response.status_code == 200:
            response = response.render()

        return response

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)

        response = self.req(user=user, status=200)
        content = response.content.decode('utf-8')

        expected = render_to_string(
            'organization/project_edit_permissions.html',
            {'project': self.project,
             'object': self.project,
             'form': forms.ProjectEditPermissions(instance=self.project)},
            request=self.request)

        assert expected == content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, status=302)
        assert ("You don't have permission to update this project"
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.req(status=302)
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        response = self.req(user=user, method='POST', status=302)

        expected_redirect = reverse(
            'organization:project-dashboard',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug
            }
        )
        assert expected_redirect in response['location']
        self.project_role.refresh_from_db()
        assert self.project_role.role == 'PM'

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, method='POST', status=302)

        assert ("You don't have permission to update this project"
                in [str(m) for m in get_messages(self.request)])
        self.project_role.refresh_from_db()
        assert self.project_role.role == 'DC'

    def test_post_with_unauthenticated_user(self):
        response = self.req(method='POST', status=302)
        assert '/account/login/' in response['location']

        self.project_role.refresh_from_db()
        assert self.project_role.role == 'DC'


class ProjectArchiveTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.ProjectArchive.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        self.prj = ProjectFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['project.*'], ['project/*/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def get(self, user=AnonymousUser()):
        setattr(self.request, 'user', user)

        return self.view(self.request,
                         organization=self.prj.organization.slug,
                         project=self.prj.slug)

    def test_archive_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        response = self.get(user)

        self.prj.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/projects/{}/'.format(
            self.prj.organization.slug, self.prj.slug) in response['location'])
        assert self.prj.archived is True

    def test_archive_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.get(user)

        self.prj.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to archive this project"
                in [str(m) for m in get_messages(self.request)])
        assert self.prj.archived is False

    def test_archive_with_unauthenticated_user(self):
        response = self.get()
        self.prj.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert self.prj.archived is False


class ProjectUnarchiveTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.ProjectUnarchive.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        self.prj = ProjectFactory.create(archived=True)

        clauses = {
            'clause': [
                clause('allow', ['project.*'], ['project/*/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def get(self, user=AnonymousUser()):
        setattr(self.request, 'user', user)

        return self.view(self.request,
                         organization=self.prj.organization.slug,
                         project=self.prj.slug)

    def test_archive_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        response = self.get(user)

        self.prj.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/projects/{}/'.format(
            self.prj.organization.slug, self.prj.slug) in response['location'])
        assert self.prj.archived is False

    def test_archive_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.get(user)

        self.prj.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to unarchive this project"
                in [str(m) for m in get_messages(self.request)])
        assert self.prj.archived is True

    def test_archive_with_unauthenticated_user(self):
        response = self.get()
        self.prj.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert self.prj.archived is True


class ProjectDataDownloadTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.ProjectDataDownload.as_view()
        self.request = HttpRequest()

        self.project = ProjectFactory.create()

        self.post_data = {'type': 'xls', 'include_resources': False}

        clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*']),
                clause('allow', ['project.download'], ['project/*/*']),
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

    def req(self, method='GET', user=AnonymousUser(), status=None):
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', method)

        if method == 'POST':
            setattr(self.request, 'POST', self.post_data)

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        response = self.view(self.request,
                             organization=self.project.organization.slug,
                             project=self.project.slug)
        if status:
            assert response.status_code == status

        return response

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        user.assign_policies(self.policy)

        response = self.req(user=user, status=200)
        content = response.render().content.decode('utf-8')

        expected = render_to_string(
            'organization/project_download.html',
            {'project': self.project,
             'object': self.project,
             'form': forms.DownloadForm(project=self.project,
                                        user=user)},
            request=self.request)

        assert expected == content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, status=302)
        assert ("You don't have permission to download data from this project"
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.req(status=302)
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        ensure_dirs()
        user = UserFactory.create()
        user.assign_policies(self.policy)
        response = self.req(user=user, method='POST', status=200)
        assert (response._headers['content-disposition'][1] ==
                'attachment; filename={}.xlsx'.format(self.project.slug))
        assert (response._headers['content-type'][1] ==
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet')

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        self.req(user=user, method='POST', status=302)
        assert ("You don't have permission to download data from this project"
                in [str(m) for m in get_messages(self.request)])

    def test_post_with_unauthenticated_user(self):
        response = self.req(method='POST', status=302)
        assert '/account/login/' in response['location']
