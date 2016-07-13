import json

from django.utils.translation import gettext as _
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from core.tests.base_test_case import UserTestCase
from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, ProjectFactory, clause
from ..models import Project, ProjectRole, OrganizationRole
from ..views import api

from tutelary.models import Role


class ProjectUsersAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
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
            name='test-policy',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

    def _get(self, org, prj, user=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{prj}/users/'
        request = APIRequestFactory().get(url.format(org=org, prj=prj))
        force_authenticate(request, user=user)
        response = self.view(request, organization=org, project=prj).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content) == length
        return content

    def _post(self, org, project, data, user=None, status=None, count=None):
        if user is None:
            user = self.user
        prj = project.slug
        url = '/v1/organizations/{org}/projects/{prj}/users/'
        request = APIRequestFactory().post(
            url.format(org=org, prj=prj), data, format='json'
        )
        force_authenticate(request, user=user)
        response = self.view(request, organization=org, project=prj).render()
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
        content = self._get(project.organization.slug, project.slug,
                            status=200, length=2)
        assert other_user.username not in [u['username'] for u in content]

    def test_full_list_with_unauthorized_user(self):
        project = ProjectFactory.create()
        self._get(project.organization.slug, project.slug,
                  user=AnonymousUser(), status=403)

    def test_get_full_list_organization_does_not_exist(self):
        project = ProjectFactory.create()
        content = self._get('some-org', project.slug, status=404)
        assert content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        organization = OrganizationFactory.create()
        content = self._get(organization.slug, '123abd', status=404)
        assert content['detail'] == _("Project not found.")

    def test_add_user(self):
        user_to_add = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user_to_add])
        project = ProjectFactory.create(organization=org)
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


class ProjectUsersDetailAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
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
            name='test-policy',
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
        response = self.view(request, organization=org, project=prj,
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
        response = self.view(request, organization=org, project=prj,
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
        prj = project.slug
        url = '/v1/organizations/{org}/projects/{prj}/users/{user}'
        request = APIRequestFactory().delete(
            url.format(org=org, prj=prj, user=user)
        )
        force_authenticate(request, user=auth)
        response = self.view(request, organization=org, project=prj,
                             username=user).render()
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert project.users.count() == count

    def test_get_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        content = self._get(project.organization.slug, project.slug,
                            user.username, status=200)
        assert content['username'] == user.username

    def test_get_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        self._get(project.organization.slug, project.slug, user.username,
                  auth=AnonymousUser(), status=403)

    def test_get_user_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        content = self._get(project.organization.slug, project.slug,
                            user.username, status=404)
        assert content['detail'] == _("User not found.")

    def test_get_user_from_org_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        content = self._get('some-org', project.slug, user.username,
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
        self._patch(project.organization.slug, project.slug,
                    user.username, {'role': 'PM'}, status=200)
        role = ProjectRole.objects.get(project=project, user=user)
        assert role.role == 'PM'

    def test_update_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        self._patch(project.organization.slug, project.slug, user.username,
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


class OrganizationProjectListAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
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
            name='test-policy',
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
        response = api.OrganizationProjectList.as_view()(request,
                                                         slug=org).render()
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
        organization = OrganizationFactory.create(slug='habitat')
        ProjectFactory.create_batch(2, organization=organization)
        ProjectFactory.create_batch(2)
        content = self._get('habitat', status=200, length=2)
        assert all([proj.get('organization').get('id') == organization.id
                    for proj in content])

    def test_full_list_with_unauthorized_user(self):
        """
        It should return all projects.
        """
        organization = OrganizationFactory.create(slug='habitat')
        ProjectFactory.create_batch(2, organization=organization)
        ProjectFactory.create_batch(2)
        content = self._get('habitat', user=AnonymousUser(),
                            status=200, length=2)
        assert all([proj.get('organization').get('id') == organization.id
                    for proj in content])

    def test_filter_active(self):
        """
        It should return only one active project.
        """
        organization = OrganizationFactory.create(slug='habitat')
        ProjectFactory.create(organization=organization, archived=True)
        ProjectFactory.create(organization=organization, archived=False)
        self._get('habitat', query='archived=True', status=200, length=1)

    def test_search_filter(self):
        """
        It should return only two matching projects.
        """
        organization = OrganizationFactory.create(slug='namati')
        ProjectFactory.create(name='opdp', organization=organization)
        content = self._get('namati', query='search=opdp',
                            status=200, length=1)
        assert all([proj['name'] == 'opdp' for proj in content])

    def test_ordering(self):
        organization = OrganizationFactory.create(slug='namati')
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
        organization = OrganizationFactory.create(slug='namati')
        ProjectFactory.create_from_kwargs([
            {'name': 'A', 'organization': organization},
            {'name': 'C', 'organization': organization},
            {'name': 'B', 'organization': organization}
        ])
        content = self._get('namati', query='ordering=-name',
                            status=200, length=3)
        names = [proj['name'] for proj in content]
        assert names == sorted(names, reverse=True)


class ProjectListAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
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
            name='test-policy',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

        self.super_user = UserFactory.create()
        su_role = Role.objects.get(name='superuser')
        self.super_user.assign_policies(su_role)

    def _get(self, user=None, query=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/projects/'
        if query is not None:
            url += '?' + query
        request = APIRequestFactory().get(url)
        if query is not None:
            setattr(request, 'GET', QueryDict(query))
        force_authenticate(request, user=user)
        response = api.ProjectList.as_view()(request).render()
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
        organization = OrganizationFactory.create(slug='habitat')
        ProjectFactory.create_batch(2, organization=organization)
        ProjectFactory.create_batch(2)
        self._get(status=200, length=4)

    def test_full_list_with_superuser(self):
        """
        It should return all projects.
        """
        organization = OrganizationFactory.create(slug='habitat')
        ProjectFactory.create_batch(2, organization=organization)
        ProjectFactory.create_batch(2)
        self._get(user=self.super_user, status=200, length=4)

    def test_full_list_with_unauthorized_user(self):
        """
        It should 403 "You do not have permission to perform this action."
        """
        OrganizationFactory.create(slug='habitat')
        content = self._get(user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_filter_active(self):
        """
        It should return only one active project.
        """
        ProjectFactory.create(archived=True)
        ProjectFactory.create(archived=False)
        self._get(query='archived=True', status=200, length=1)

    def test_search_filter(self):
        """
        It should return only two matching projects.
        """
        ProjectFactory.create(name='opdp')
        ProjectFactory.create_batch(3)
        content = self._get(query='search=opdp', status=200, length=1)
        assert all([proj['name'] == 'opdp' for proj in content])

    def test_ordering(self):
        ProjectFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        content = self._get(query='ordering=name', status=200, length=3)
        names = [proj['name'] for proj in content]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        ProjectFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        content = self._get(query='ordering=-name', status=200, length=3)
        names = [proj['name'] for proj in content]
        assert names == sorted(names, reverse=True)

    # CONDITIONS:
    #
    # 1. All public projects should be visible to all users.
    # 2. Private projects should be visible to all users who are
    #    members of the organization owning the project.
    # 3. No private project should be visible to any user who is not a
    #    member of the organization owning the project.
    #
    #                 ORG 0    ORG 1    ORG 2
    # user0
    # user1             X
    # user2                      X
    # user3                               X
    # user4             X        X
    # user5             X                 X
    # user6                      X        X
    # user7             X        X        X
    #
    # prj0 (PUBLIC)     X
    # prj1 (PRIVATE     X
    # prj2 (PUBLIC)              X
    # prj3 (PRIVATE              X
    # prj4 (PUBLIC)                       X
    # prj5 (PRIVATE                       X
    #
    # user0 can access projects 0   2   4
    # user1 can access projects 0 1 2   4
    # user2 can access projects 0   2 3 4
    # user3 can access projects 0   2   4 5
    # user4 can access projects 0 1 2 3 4
    # user5 can access projects 0 1 2   4 5
    # user6 can access projects 0   2 3 4 5
    # user7 can access projects 0 1 2 3 4 5

    def _check_visible(self, users, orgs, prjs, user, idxs):
        content = self._get(user=user, status=200)
        expected_names = [prjs[i].name for i in idxs]
        pnames = [p['name'] for p in content]
        assert(sorted(expected_names) == sorted(pnames))

    def test_visibility_filtering(self):
        users = UserFactory.create_batch(8)
        clause = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['organization/*'],
                    'action': ['project.list']
                },
                {
                    'effect': 'allow',
                    'object': ['project/*/*'],
                    'action': ['project.view']
                }
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clause)
        )
        for user in users:
            user.assign_policies(policy)
        orgs = [
            OrganizationFactory.create(
                add_users=[users[1], users[4], users[5], users[7]]
            ),
            OrganizationFactory.create(
                add_users=[users[2], users[4], users[6], users[7]]
            ),
            OrganizationFactory.create(
                add_users=[users[3], users[5], users[6], users[7]]
            )
        ]
        prjs = [
            ProjectFactory.create(organization=orgs[0], access='public'),
            ProjectFactory.create(organization=orgs[0], access='private'),
            ProjectFactory.create(organization=orgs[1], access='public'),
            ProjectFactory.create(organization=orgs[1], access='private'),
            ProjectFactory.create(organization=orgs[2], access='public'),
            ProjectFactory.create(organization=orgs[2], access='private')
        ]
        self._check_visible(users, orgs, prjs, users[0], [0,    2,    4])
        self._check_visible(users, orgs, prjs, users[1], [0, 1, 2,    4])
        self._check_visible(users, orgs, prjs, users[2], [0,    2, 3, 4])
        self._check_visible(users, orgs, prjs, users[3], [0,    2,    4, 5])
        self._check_visible(users, orgs, prjs, users[4], [0, 1, 2, 3, 4])
        self._check_visible(users, orgs, prjs, users[5], [0, 1, 2,    4, 5])
        self._check_visible(users, orgs, prjs, users[6], [0,    2, 3, 4, 5])
        self._check_visible(users, orgs, prjs, users[7], [0, 1, 2, 3, 4, 5])


class ProjectCreateAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*', 'org.*.*', 'project.*'],
                       ['organization/*']),
                clause('allow', ['project.*'], ['project/*/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def _post(self, org, data, user=None, status=None, count=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/'
        request = APIRequestFactory().post(url.format(org=org), data)
        force_authenticate(request, user=user)
        response = api.OrganizationProjectList.as_view()(
            request, slug=org
        ).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert Project.objects.count() == count
        return content

    def test_create_valid_project(self):
        OrganizationFactory.create(slug='habitat')
        data = {
            'name': 'Project',
            'description': 'Project description',
        }
        self._post('habitat', data, status=201, count=1)

    def test_create_invalid_project(self):
        OrganizationFactory.create(slug='namati')
        data = {
            'description': 'Project description'
        }
        content = self._post('namati', data, status=400, count=0)
        assert content['name'][0] == _('This field is required.')


class ProjectDetailAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
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
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

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
        self.restricted_user = UserFactory.create()
        assign_user_policies(self.restricted_user, restricted_policy)

    def _get(self, org, slug, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{slug}'
        request = APIRequestFactory().get(url.format(org=org, slug=slug))
        force_authenticate(request, user=user)
        response = self.view(request, organization=org, project=slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, org, project, data, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/organizations/{org}/projects/{slug}/'
        request = APIRequestFactory().patch(
            url.format(org=org, slug=project.slug), data
        )
        force_authenticate(request, user=user)
        response = self.view(request, organization=org,
                             project=project.slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        project.refresh_from_db()
        return content

    def _test_objs(self, archived=False, access='public'):
        organization = OrganizationFactory.create(slug='namati')
        project = ProjectFactory.create(slug='project',
                                        organization=organization,
                                        name='Test Project',
                                        archived=archived,
                                        access=access)
        return (organization, project)

    def _test_get_public_project(self, user, status,
                                 check_ok=False, check_error=False,
                                 non_existent=False):
        organization, project = self._test_objs()
        slug = project.slug
        if non_existent:
            slug = 'some-project'
        content = self._get('namati', slug, user=user, status=status)
        if check_ok:
            assert content['id'] == project.id
            assert 'users' in content
        if check_error:
            assert content['detail'] == PermissionDenied.default_detail
        if non_existent:
            assert content['detail'] == _("Project not found.")

    def test_get_public_project_with_valid_user(self):
        self._test_get_public_project(self.user, 200, check_ok=True)

    def test_get_public_project_with_unauthorized_user(self):
        self._test_get_public_project(AnonymousUser(), 200, check_ok=True)

    def test_get_public_project_that_does_not_exist(self):
        self._test_get_public_project(self.user, 404, non_existent=True)

    def _test_get_private_project(self, status=None, user=None,
                                  check_ok=False, check_error=False,
                                  make_org_member=False,
                                  make_other_org_member=False,
                                  remove_org_member=False):
        if user is None:
            user = self.user
        org, prj = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if remove_org_member:
            OrganizationRole.objects.filter(
                organization=org, user=user
            ).delete()
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        cont = self._get('namati', prj.slug, user=user, status=status)
        if check_ok:
            assert cont['id'] == prj.id
            assert 'users' in cont
        if check_error:
            assert cont['detail'] == PermissionDenied.default_detail

    def test_get_private_project(self):
        self._test_get_private_project(
            status=200, check_ok=True
        )

    def test_get_private_project_with_unauthorized_user(self):
        self._test_get_private_project(
            user=AnonymousUser(), status=403, check_error=True
        )

    def test_get_private_project_without_permission(self):
        self._test_get_private_project(
            user=self.restricted_user, status=403, check_error=True
        )

    def test_get_private_project_based_on_org_membership(self):
        self._test_get_private_project(
            user=UserFactory.create(), status=200, check_ok=True,
            make_org_member=True
        )

    def test_get_private_project_with_other_org_membership(self):
        self._test_get_private_project(
            user=UserFactory.create(), status=403, check_error=True,
            make_other_org_member=True
        )

    def test_get_private_project_on_org_membership_removal(self):
        self._test_get_private_project(
            user=UserFactory.create(), status=403, check_error=True,
            make_org_member=True, remove_org_member=True
        )

    def test_valid_update(self):
        organization, project = self._test_objs()
        self._patch('namati', project, {'name': 'OPDP'}, status=200)
        assert project.name == 'OPDP'

    def test_update_with_unauthorized_user(self):
        organization, project = self._test_objs()
        self._patch('namati', project, {'name': 'OPDP'}, status=403,
                    user=AnonymousUser())
        assert project.name == 'Test Project'

    def test_invalid_update(self):
        organization, project = self._test_objs()
        content = self._patch('namati', project, {'name': ''}, status=400)
        assert project.name == 'Test Project'
        assert content['name'][0] == _('This field may not be blank.')

    def test_archive(self):
        organization, project = self._test_objs(archived=False)
        self._patch('namati', project, {'archived': True}, status=200)
        assert project.archived

    def test_unarchive(self):
        organization, project = self._test_objs(archived=True)
        self._patch('namati', project, {'archived': False}, status=200)
        assert not project.archived

    def test_valid_visibility_patching(self):
        # Create users with default list and view permissions for
        # organizations and projects.
        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view', 'project.list'],
                       ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses)
        )
        org_user = UserFactory.create()
        assign_user_policies(org_user, policy)
        non_org_user = UserFactory.create()
        assign_user_policies(non_org_user, policy)

        # Create organization, adding just one user.
        org = OrganizationFactory.create(add_users=[org_user])

        # Create public project in organization.
        prj = ProjectFactory.create(organization=org, access='public')

        # User in org SHOULD be able to see project.
        self._get(org.slug, prj.slug, user=org_user, status=200)
        # User NOT in org SHOULD be able to see project.
        self._get(org.slug, prj.slug, user=non_org_user, status=200)

        # Patch visibility to private.
        self._patch(org.slug, prj, {'access': 'private'}, status=200)

        # User in org SHOULD be able to see project.
        self._get(org.slug, prj.slug, user=org_user, status=200)
        # User not in org SHOULD NOT be able to see project.
        self._get(org.slug, prj.slug, user=non_org_user, status=403)

        # Patch visibility to public.
        self._patch(org.slug, prj, {'access': 'public'}, status=200)

        # User in org SHOULD be able to see project.
        self._get(org.slug, prj.slug, user=org_user, status=200)
        # User NOT in org SHOULD be able to see project.
        self._get(org.slug, prj.slug, user=non_org_user, status=200)

    def test_invalid_visibility_patching(self):
        organization, project = self._test_objs(archived=True)
        self._patch('namati', project, {'access': 'something'}, status=400)
        assert project.access == 'public'
