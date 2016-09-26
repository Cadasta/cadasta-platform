import json
import os
import os.path
import pytest

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpRequest, Http404
from django.template.loader import render_to_string
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser

from tutelary.models import Policy, Role, assign_user_policies
from buckets.test.storage import FakeS3Storage
from skivvy import ViewTestCase

from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from organization.models import OrganizationRole, Project, ProjectRole
from questionnaires.tests.factories import QuestionnaireFactory
from questionnaires.tests.utils import get_form
from questionnaires.models import Questionnaire
from resources.tests.utils import clear_temp  # noqa
from resources.utils.io import ensure_dirs

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
            'is_superuser': False
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
                                        admin=True)
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
            is_superuser=True
        )


class ProjectDashboardTest(ViewTestCase, UserTestCase, TestCase):
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
            'geojson': '{"type": "FeatureCollection", "features": []}',
            'is_superuser': False,
            'is_administrator': False
        }

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_get_with_authorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(has_content=False,
                                       num_locations=0,
                                       num_parties=0,
                                       num_resources=0,
                                       is_allowed_add_location=False)
        assert response.content == expected

    def test_get_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 200
        expected = self.render_content(has_content=False,
                                       num_locations=0,
                                       num_parties=0,
                                       num_resources=0,
                                       is_allowed_add_location=False)
        assert response.content == expected

    def test_get_with_superuser(self):
        superuser_role = Role.objects.get(name='superuser')
        self.user.assign_policies(superuser_role)
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(is_superuser=True,
                                       is_administrator=True,
                                       is_allowed_add_location=True,
                                       is_allowed_add_resource=True)
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
                                       is_allowed_add_resource=True)
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
        expected = self.render_content(has_content=False,
                                       num_locations=0,
                                       num_parties=0,
                                       num_resources=0,
                                       is_allowed_add_location=False)
        assert response.content == expected

    def test_get_private_project(self):
        self.project.access = 'private'
        self.project.save()
        response = self.request(user=self.user)
        assert response.status_code == 200
        expected = self.render_content(has_content=False,
                                       num_locations=0,
                                       num_parties=0,
                                       num_resources=0,
                                       is_allowed_add_location=False)
        assert response.content == expected

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
        expected = self.render_content(has_content=False,
                                       num_locations=0,
                                       num_parties=0,
                                       num_resources=0,
                                       is_allowed_add_location=False)
        assert response.content == expected

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
                                       is_allowed_add_resource=True)
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
                                       is_allowed_add_resource=True)
        assert response.content == expected


@pytest.mark.usefixtures('make_dirs')
class ProjectAddTest(UserTestCase, TestCase):
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

    def _get_xls_form(self, form_name):
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
        'details-contacts-0-name': "John Lennon",
        'details-contacts-0-email': 'john@beatles.co.uk',
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
        self.DETAILS_POST_DATA['details-questionnaire'] = self._get_xls_form(
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
        self.DETAILS_POST_DATA['wizard_goto_step'] = 'extents'
        details_response = self.client.post(
            reverse('project:add'), self.DETAILS_POST_DATA
        )
        assert details_response.status_code == 200

    def test_flow_with_archived_organization(self):
        self.org.archived = True
        self.org.save()
        OrganizationRole.objects.create(organization=self.org,
                                        user=self.users[0],
                                        admin=True)

        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        with pytest.raises(KeyError):
            self.client.post(
                reverse('project:add'), self.DETAILS_POST_DATA
            )

    def test_full_flow_invalid_xlsform(self):
        self.client.force_login(self.users[0])
        extents_response = self.client.post(
            reverse('project:add'), self.EXTENTS_POST_DATA
        )
        assert extents_response.status_code == 200
        details_post_data = self.DETAILS_POST_DATA.copy()
        details_post_data[
            'details-questionnaire'] = self._get_xls_form(
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
        self.DETAILS_POST_DATA['details-questionaire'] = self._get_xls_form(
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
                'form': forms.ProjectAddExtents(instance=self.project)}

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
class ProjectEditDetailsTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ProjectEditDetails
    template = 'organization/project_edit_details.html'
    success_url_name = 'organization:project-dashboard'
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
                'form': forms.ProjectEditDetails(instance=self.project)}

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_authorized_user_include_questionnaire(self):
        questionnaire = QuestionnaireFactory.create(project=self.project)
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
        response = self.request(user=user, method='POST')

        assert response.status_code == 302
        assert self.expected_success_url in response.location
        self.project.refresh_from_db()
        assert self.project.name == self.post_data['name']
        assert self.project.description == self.post_data['description']

    def test_post_invalid_form(self):
        question = get_form('xls-form-invalid')
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
        # form.add_error('questionnaire',
        #                "'interger' is not an accepted question type")
        # form.add_error('questionnaire',
        #                "'select multiple list' is not an accepted question "
        #                "type")

        assert response.status_code == 200
        assert response.content == self.render_content(form=form)

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
                'form': forms.ProjectEditPermissions(instance=self.project)}

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
                                           user=self.user)}

    def test_get_with_authorized_user(self):
        assign_policies(self.user)

        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert ("You don't have permission to download data from this project"
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
        assert ("You don't have permission to download data from this project"
                in response.messages)

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert '/account/login/' in response.location
