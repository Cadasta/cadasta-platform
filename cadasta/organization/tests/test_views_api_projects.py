import json

from django.test import TestCase
from django.utils.translation import gettext as _
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, ProjectFactory, clause
from ..models import Project, ProjectRole
from ..views import api


class ProjectUsersAPITest(TestCase):
    def setUp(self):
        self.view = api.ProjectUsers.as_view()

        clause = {
            'clause': [
                {
                    "effect": "allow",
                    "object": ["*"],
                    "action": ["org.*"]
                }, {
                    'effect': 'allow',
                    'object': ['organization/*'],
                    'action': ['org.*', "org.*.*"]
                }, {
                    'effect': 'allow',
                    'object': ['project/*/*'],
                    'action': ['project.*', 'project.*.*']
                }
            ]
        }
        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

    def _get(self, org, prj, user=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{prj}/users/'
        request = APIRequestFactory().get(url.format(org=org, prj=prj))
        force_authenticate(request, user=user)
        response = self.view(request, slug=org, project_id=prj).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content) == length
        return content

    def _post(self, org, project, data, user=None, status=None, count=None):
        if user is None:
            user = self.user
        prj = project.id
        url = '/v1/organizations/{org}/projects/{prj}/users/'
        request = APIRequestFactory().post(
            url.format(org=org, prj=prj), data, format='json'
        )
        force_authenticate(request, user=user)
        response = self.view(request, slug=org, project_id=prj).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert project.users.count() == count
        return content

    def test_full_list(self):
        """
        It should return all organizations.
        """
        prj_users = UserFactory.create_batch(2)
        other_user = UserFactory.create()
        project = ProjectFactory.create(add_users=prj_users)
        content = self._get(project.organization.slug, project.id,
                            status=200, length=2)
        assert other_user.username not in [u['username'] for u in content]

    def test_full_list_with_unauthorized_user(self):
        project = ProjectFactory.create()
        self._get(project.organization.slug, project.id,
                  user=AnonymousUser(), status=403)

    def test_get_full_list_organization_does_not_exist(self):
        project = ProjectFactory.create()
        content = self._get('some-org', project.id, status=404)
        assert content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        organization = OrganizationFactory.create()
        content = self._get(organization.slug, '123abd', status=404)
        assert content['detail'] == _("Project not found.")

    def test_add_user(self):
        user_to_add = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user_to_add])
        project = ProjectFactory.create(**{'organization': org})
        self._post(project.organization.slug, project,
                   {'username': user_to_add.username}, status=201, count=1)

    def test_add_user_with_unauthorized_user(self):
        user_to_add = UserFactory.create()
        project = ProjectFactory.create()
        self._post(project.organization.slug, project,
                   {'username': user_to_add.username},
                   user=AnonymousUser(), status=403, count=0)

    def test_add_user_with_invalid_data(self):
        project = ProjectFactory.create()
        content = self._post(project.organization.slug, project,
                             {'username': 'some-user'}, status=400, count=0)
        assert (_('User with username or email some-user does not exist')
                in content['username'])


class ProjectUsersDetailTest(TestCase):
    def setUp(self):
        self.view = api.ProjectUsersDetail.as_view()

        clause = {
            'clause': [
                {
                    "effect": "allow",
                    "object": ["*"],
                    "action": ["org.*"]
                }, {
                    'effect': 'allow',
                    'object': ['organization/*'],
                    'action': ['org.*', "org.*.*"]
                }, {
                    'effect': 'allow',
                    'object': ['project/*/*'],
                    'action': ['project.*', 'project.*.*']
                }
            ]
        }
        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

    def _get(self, org, prj, user, auth=None, status=None):
        if auth is None:
            auth = self.user
        url = '/v1/organizations/{org}/projects/{prj}/users/{user}'
        request = APIRequestFactory().get(
            url.format(org=org, prj=prj, user=user)
        )
        force_authenticate(request, user=auth)
        response = self.view(request, slug=org, project_id=prj,
                             username=user).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, org, prj, user, data, auth=None, status=None):
        if auth is None:
            auth = self.user
        url = '/v1/organizations/{org}/projects/{prj}/users/{user}'
        request = APIRequestFactory().patch(
            url.format(org=org, prj=prj, user=user),
            data, format='json'
        )
        force_authenticate(request, user=auth)
        response = self.view(request, slug=org, project_id=prj,
                             username=user).render()
        content = None
        if len(response.content) > 0:
            content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _delete(self, org, project, user, auth=None, status=None, count=None):
        if auth is None:
            auth = self.user
        prj = project.id
        url = '/v1/organizations/{org}/projects/{prj}/users/{user}'
        request = APIRequestFactory().delete(
            url.format(org=org, prj=prj, user=user)
        )
        force_authenticate(request, user=auth)
        response = self.view(request, slug=org, project_id=prj,
                             username=user).render()
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert project.users.count() == count

    def test_get_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        content = self._get(project.organization.slug, project.id,
                            user.username, status=200)
        assert content['username'] == user.username

    def test_get_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        self._get(project.organization.slug, project.id, user.username,
                  auth=AnonymousUser(), status=403)

    def test_get_user_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        content = self._get(project.organization.slug, project.id,
                            user.username, status=404)
        assert content['detail'] == _("User not found.")

    def test_get_user_from_org_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        content = self._get('some-org', project.id, user.username,
                            status=404)
        assert content['detail'] == _("Project not found.")

    def test_get_user_from_project_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        content = self._get(project.organization.slug, 'abc123',
                            user.username, status=404)
        assert content['detail'] == _("Project not found.")

    def test_update_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        self._patch(project.organization.slug, project.id,
                    user.username, {'role': 'PM'}, status=200)
        role = ProjectRole.objects.get(project=project, user=user)
        assert role.role == 'PM'

    def test_update_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        self._patch(project.organization.slug, project.id, user.username,
                    {'role': 'PM'}, auth=AnonymousUser(), status=403)
        role = ProjectRole.objects.get(project=project, user=user)
        assert role.role == 'PU'

    def test_delete_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        self._delete(project.organization.slug, project, user.username,
                     status=204, count=0)

    def test_delete_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        self._delete(project.organization.slug, project, user.username,
                     auth=AnonymousUser(), status=403, count=1)


class ProjectListAPITest(TestCase):
    def setUp(self):
        clause = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['organization/*'],
                    'action': ['project.list']
                }
            ]
        }
        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def _get(self, org, user=None, query=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/'
        if query is not None:
            url += '?' + query
        request = APIRequestFactory().get(url.format(org=org))
        if query is not None:
            setattr(request, 'GET', QueryDict(query))
        force_authenticate(request, user=user)
        response = api.ProjectList.as_view()(request, slug=org).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content) == length
        return content

    def test_full_list(self):
        """
        It should return all projects.
        """
        organization = OrganizationFactory.create(**{'slug': 'habitat'})
        ProjectFactory.create_batch(2, **{'organization': organization})
        ProjectFactory.create_batch(2)
        content = self._get('habitat', status=200, length=2)
        assert all([proj.get('organization').get('id') == organization.id
                    for proj in content])

    def test_full_list_with_unautorized_user(self):
        """
        It should 403 "You do not have permission to perform this action."
        """
        OrganizationFactory.create(**{'slug': 'habitat'})
        content = self._get('habitat', user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_filter_active(self):
        """
        It should return only one active project.
        """
        organization = OrganizationFactory.create(**{'slug': 'habitat'})
        ProjectFactory.create(**{'organization': organization,
                                 'archived': True})
        ProjectFactory.create(**{'organization': organization,
                                 'archived': False})
        self._get('habitat', query='archived=True', status=200, length=1)

    def test_search_filter(self):
        """
        It should return only two matching projects.
        """
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        ProjectFactory.create(**{'name': 'opdp', 'organization':
                                 organization})
        content = self._get('namati', query='search=opdp',
                            status=200, length=1)
        assert all([proj['name'] == 'opdp' for proj in content])

    def test_ordering(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        ProjectFactory.create_from_kwargs([
            {'name': 'A', 'organization': organization},
            {'name': 'B', 'organization': organization},
            {'name': 'C', 'organization': organization}
        ])
        content = self._get('namati', query='ordering=name',
                            status=200, length=3)
        names = [proj['name'] for proj in content]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        ProjectFactory.create_from_kwargs([
            {'name': 'A', 'organization': organization},
            {'name': 'C', 'organization': organization},
            {'name': 'B', 'organization': organization}
        ])
        content = self._get('namati', query='ordering=-name',
                            status=200, length=3)
        names = [proj['name'] for proj in content]
        assert names == sorted(names, reverse=True)


class ProjectCreateAPITest(TestCase):
    def setUp(self):
        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*', 'org.*.*', 'project.*'],
                       ['organization/*']),
                clause('allow', ['project.*'], ['project/*/*'])
            ]
        }
        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def _post(self, org, data, user=None, status=None, count=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/'
        request = APIRequestFactory().post(url.format(org=org), data)
        force_authenticate(request, user=user)
        response = api.ProjectList.as_view()(request, slug=org).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert Project.objects.count() == count
        return content

    def test_create_valid_project(self):
        OrganizationFactory.create(**{'slug': 'habitat'})
        data = {
            'name': 'Project',
            'description': 'Project description',
        }
        self._post('habitat', data, status=201, count=1)

    def test_create_invalid_project(self):
        OrganizationFactory.create(**{'slug': 'namati'})
        data = {
            'description': 'Project description'
        }
        content = self._post('namati', data, status=400, count=0)
        assert content['name'][0] == _('This field is required.')


class ProjectDetailTest(TestCase):
    def setUp(self):
        self.view = api.ProjectDetail.as_view()
        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*', 'org.*.*', 'project.*'],
                       ['organization/*']),
                clause('allow', ['project.*'], ['project/*/*'])
            ]
        }
        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def _get(self, org, slug, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{slug}'
        request = APIRequestFactory().get(url.format(org=org, slug=slug))
        force_authenticate(request, user=user)
        response = self.view(request, slug=org, project_slug=slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, org, slug, data, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{slug}/'
        request = APIRequestFactory().patch(url.format(org=org, slug=slug),
                                            data)
        force_authenticate(request, user=user)
        response = self.view(request, slug=org, project_slug=slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def test_get_project(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        project = ProjectFactory.create(**{'project_slug': 'project',
                                           'organization': organization})
        content = self._get('namati', project.project_slug, status=200)
        assert content['id'] == project.id
        assert 'users' in content

    def test_get_project_with_unauthorized_user(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        project = ProjectFactory.create(**{'project_slug': 'project',
                                           'organization': organization})
        content = self._get('namati', project.project_slug,
                            user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_get_project_that_does_not_exist(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        ProjectFactory.create(**{'project_slug': 'namati-project',
                                 'organization': organization})
        content = self._get('namati', 'some-project', status=404)
        assert content['detail'] == _("Project not found.")

    def test_valid_update(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        project = ProjectFactory.create(**{'project_slug': 'namati-project',
                                           'organization': organization})
        self._patch('namati', project.project_slug, {'name': 'OPDP'},
                    status=200)
        project.refresh_from_db()
        assert project.name == 'OPDP'

    def test_update_with_unauthorized_user(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        project = ProjectFactory.create(**{'name': 'OPDP',
                                           'project_slug': 'namati-project',
                                           'organization': organization})
        self._patch('namati', project.project_slug, {'name': 'OPDP'},
                    user=AnonymousUser(), status=403)
        project.refresh_from_db()
        assert project.name == "OPDP"

    def test_invalid_update(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        project = ProjectFactory.create(**{'name': 'OPDP',
                                           'project_slug': 'namati-project',
                                           'organization': organization})
        content = self._patch('namati', project.project_slug, {'name': ''},
                              status=400)
        project.refresh_from_db()
        assert project.name == 'OPDP'
        assert content['name'][0] == _('This field may not be blank.')

    def test_archive(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        project = ProjectFactory.create(**{'project_slug': 'namati-project',
                                           'organization': organization})
        self._patch('namati', project.project_slug, {'archived': True},
                    status=200)
        project.refresh_from_db()
        assert project.archived

    def test_unarchive(self):
        organization = OrganizationFactory.create(**{'slug': 'namati'})
        project = ProjectFactory.create(**{'project_slug': 'namati-project',
                                           'organization': organization,
                                           'archived': True})
        self._patch('namati', project.project_slug, {'archived': False},
                    status=200)
        project.refresh_from_db()
        assert not project.archived
