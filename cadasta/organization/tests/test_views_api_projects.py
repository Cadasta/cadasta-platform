import json

from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from accounts.models import User
from .factories import OrganizationFactory, ProjectFactory, clause
from ..models import Project, ProjectRole, OrganizationRole
from ..views import api

from tutelary.models import Role


def assign_policies(user, add_clauses=None):
    clause = {
        'clause': [
            {
                "effect": "allow",
                "object": ["*"],
                "action": ["org.*"]
            }, {
                'effect': 'allow',
                'object': ['organization/*'],
                'action': ['org.*', "org.*.*", "project.*"]
            }, {
                'effect': 'allow',
                'object': ['project/*/*'],
                'action': ['project.*', 'project.*.*']
            },
        ],
    }

    if add_clauses:
        clause['clause'] += add_clauses

    policy = Policy.objects.create(
        name='test-policy',
        body=json.dumps(clause))
    user.assign_policies(policy)


class ProjectUsersAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.ProjectUsers

    def setup_models(self):
        self.user = UserFactory.create()
        self.oa_group = Group.objects.get(name='OrgAdmin')
        self.om_group = Group.objects.get(name='OrgMember')
        self.pm_group = Group.objects.get(name='ProjectManager')
        self.pu_group = Group.objects.get(name='ProjectMember')

    def setup_url_kwargs(self):
        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }

    def test_full_list(self):
        """It should return all users."""
        prj_users = UserFactory.create_batch(2)
        other_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=prj_users)
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 2
        assert (other_user.username not in
                [u['username'] for u in response.content['results']])

    def test_full_list_with_unauthorized_user(self):
        self.project = ProjectFactory.create()
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_full_list_organization_does_not_exist(self):
        self.project = ProjectFactory.create()
        response = self.request(url_kwargs={'organization': 'some-org'},
                                user=self.user)
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        self.project = ProjectFactory.create()
        response = self.request(url_kwargs={'project': '123abc'},
                                user=self.user)
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_add_user(self):
        user_to_add = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user_to_add])
        self.project = ProjectFactory.create(organization=org)
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(post_data={'username': user_to_add.username},
                                method='POST',
                                user=self.user)
        assert response.status_code == 201
        assert self.project.users.count() == 2

    def test_add_user_when_role_exists(self):
        new_user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[new_user])
        self.project = ProjectFactory.create(organization=org)
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        ProjectRole.objects.create(
            user=new_user, project=self.project,
            group=self.pu_group, role='PU')
        response = self.request(user=self.user, method='POST',
                                post_data={'username': new_user.username})
        assert response.status_code == 400

    def test_add_user_with_unauthorized_user(self):
        user_to_add = UserFactory.create()
        self.project = ProjectFactory.create()
        response = self.request(post_data={'username': user_to_add.username},
                                method='POST')
        assert response.status_code == 403
        assert self.project.users.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_add_user_with_invalid_data(self):
        self.project = ProjectFactory.create()
        ProjectRole.objects.create(
            user=self.user, project=self.project,
            group=self.pm_group, role='PM')
        response = self.request(post_data={'username': 'some-user'},
                                method='POST',
                                user=self.user)
        assert response.status_code == 400
        assert self.project.users.count() == 1
        assert ('User with username or email some-user does not exist'
                in response.content['username'])

    def test_add_user_to_archived_project(self):
        user_to_add = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user_to_add])
        self.project = ProjectFactory.create(organization=org)
        self.project.archived = True
        self.project.save()

        response = self.request(post_data={'username': user_to_add.username},
                                method='POST',
                                user=self.user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert self.project.users.count() == 0


class ProjectUsersDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.ProjectUsersDetail
    post_data = {'role': 'PM'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.pm_group = Group.objects.get(name='ProjectManager')

    def setup_url_kwargs(self):
        username = 'blah'
        if hasattr(self, 'test_user'):
            username = self.test_user.username

        return {
            'organization': self.project.organization.slug,
            'project': self.project.slug,
            'username': username
        }

    def test_get_user(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['username'] == self.test_user.username

    def test_get_user_with_unauthorized_user(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        response = self.request()
        assert response.status_code == 403

    def test_get_user_that_does_not_exist(self):
        self.project = ProjectFactory.create()
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(user=self.user,
                                url_kwargs={'username': self.user.username})
        assert response.status_code == 404
        assert response.content['detail'] == "User not found."

    def test_get_user_from_org_that_does_not_exist(self):
        self.project = ProjectFactory.create()
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_user_from_project_that_does_not_exist(self):
        self.project = ProjectFactory.create()
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_update_user(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        role = ProjectRole.objects.get(project=self.project,
                                       user=self.test_user)
        assert role.role == 'PM'

    def test_PATCH_user_with_unauthorized_user(self):
        user = UserFactory.create()
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        response = self.request(method='PATCH', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        role = ProjectRole.objects.get(project=self.project,
                                       user=self.test_user)
        assert role.role == 'PU'

    def test_PATCH_user_with_anonymous_user(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        role = ProjectRole.objects.get(project=self.project,
                                       user=self.test_user)
        assert role.role == 'PU'

    def test_PUT_user_with_unauthorized_user(self):
        user = UserFactory.create()
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        response = self.request(method='PUT', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        role = ProjectRole.objects.get(project=self.project,
                                       user=self.test_user)
        assert role.role == 'PU'

    def test_PUT_user_with_anonymous_user(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        response = self.request(method='PUT')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        role = ProjectRole.objects.get(project=self.project,
                                       user=self.test_user)
        assert role.role == 'PU'

    def test_update_user_with_archived_project(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        self.project.archived = True
        self.project.save()
        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        role = ProjectRole.objects.get(project=self.project,
                                       user=self.test_user)
        assert role.role == 'PU'

    def test_delete_user(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        ProjectRole.objects.create(
            project=self.project, user=self.user,
            group=self.pm_group, role='PM')
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert self.project.users.count() == 1
        assert User.objects.filter(username=self.test_user.username).exists()

    def test_delete_user_with_unauthorized_user(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert self.project.users.count() == 1

    def test_delete_user_in_archived_project(self):
        self.test_user = UserFactory.create()
        self.project = ProjectFactory.create(add_users=[self.test_user])
        self.project.archived = True
        self.project.save()
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert self.project.users.count() == 1


class OrganizationProjectListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.OrganizationProjectList
    url_kwargs = {'organization': 'habitat'}

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.organization = OrganizationFactory.create(slug='habitat')

    def test_full_list(self):
        """
        It should return all projects.
        """
        ProjectFactory.create_batch(2, organization=self.organization)
        ProjectFactory.create_batch(2)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 2
        assert all([proj.get('organization').get('id') == self.organization.id
                    for proj in response.content['results']])

    def test_empty_list(self):
        """
        It should return an empty array.
        """
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['results'] == []

    def test_full_list_with_unauthorized_user(self):
        """
        It should return all projects.
        """
        ProjectFactory.create_batch(2, organization=self.organization)
        ProjectFactory.create_batch(2)
        response = self.request()
        assert response.status_code == 200
        assert len(response.content['results']) == 2
        assert all([proj.get('organization').get('id') == self.organization.id
                    for proj in response.content['results']])

    def test_filter_archived_without_authorization(self):
        """
        It should return zero archived project.
        """
        ProjectFactory.create(organization=self.organization, archived=True)
        ProjectFactory.create(organization=self.organization, archived=False)
        response = self.request(user=self.user, get_data={'archived': True})
        assert response.status_code == 200
        assert len(response.content['results']) == 0

    def test_fitler_archived_with_org_admin(self):
        """
        It should return one archived project.
        """
        user = UserFactory.create()
        OrganizationRole.objects.create(
            organization=self.organization, user=user, admin=True)
        ProjectFactory.create(organization=self.organization, archived=True)
        ProjectFactory.create(organization=self.organization, archived=False)
        response = self.request(user=user, get_data={'archived': True})
        assert response.status_code == 200
        assert len(response.content['results']) == 1

    def test_search_filter(self):
        """
        It should return only two matching projects.
        """
        ProjectFactory.create(organization=self.organization, name='opdp',)
        ProjectFactory.create(organization=self.organization, name='aaaa',)
        response = self.request(user=self.user, get_data={'search': 'opdp'})
        assert response.status_code == 200
        assert len(response.content['results']) == 1
        assert all([proj['name'] == 'opdp' for proj in
                    response.content['results']])

    def test_ordering(self):
        ProjectFactory.create_from_kwargs([
            {'name': 'A', 'organization': self.organization},
            {'name': 'B', 'organization': self.organization},
            {'name': 'C', 'organization': self.organization}
        ])
        response = self.request(user=self.user, get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [proj['name'] for proj in response.content['results']]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        ProjectFactory.create_from_kwargs([
            {'name': 'A', 'organization': self.organization},
            {'name': 'C', 'organization': self.organization},
            {'name': 'B', 'organization': self.organization}
        ])
        response = self.request(user=self.user, get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [proj['name'] for proj in response.content['results']]
        assert names == sorted(names, reverse=True)

    def test_permission_filter(self):
        addtional_clause = [{
            'effect': 'allow',
            'object': ['project/*/*'],
            'action': ['party.create']
        }, {
            'effect': 'deny',
            'object': ['project/*/unauthorized'],
            'action': ['party.create']
        }]

        ProjectFactory.create_from_kwargs([
            {'slug': 'unauthorized', 'organization': self.organization},
            {'organization': self.organization}
        ])

        assign_policies(self.user, add_clauses=addtional_clause)

        response = self.request(user=self.user,
                                get_data={'permissions': 'party.create'})
        assert response.status_code == 200
        assert len(response.content['results']) == 1
        assert response.content['results'][0]['slug'] != 'unauthorized'


class ProjectListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.ProjectList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.organization = OrganizationFactory.create(slug='habitat')

    def test_full_list(self):
        """
        It should return all projects.
        """
        ProjectFactory.create_batch(2, organization=self.organization)
        ProjectFactory.create_batch(2)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 4

    def test_full_list_with_superuser(self):
        """
        It should return all projects.
        """
        super_user = UserFactory.create()
        su_role = Role.objects.get(name='superuser')
        super_user.assign_policies(su_role)

        ProjectFactory.create_batch(2, organization=self.organization)
        ProjectFactory.create_batch(2)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 4

    def test_full_list_with_unauthorized_user(self):
        """
        It should return projects without member information.
        """
        ProjectFactory.create_batch(2, organization=self.organization)
        ProjectFactory.create_batch(2)
        response = self.request()
        assert response.status_code == 200
        assert len(response.content['results']) == 4
        assert all(['users' not in proj['organization']
                    for proj in response.content['results']])

    def test_empty_list_with_unauthorized_user(self):
        """
        It should 403 "You do not have permission to perform this action."
        """
        response = self.request()
        assert response.status_code == 200
        assert len(response.content['results']) == 0

    def test_filter_active(self):
        """
        It should return only one active project.
        """
        ProjectFactory.create(archived=True)
        ProjectFactory.create(archived=False)
        response = self.request(user=self.user, get_data={'archived': False})
        assert response.status_code == 200
        assert len(response.content['results']) == 1

    def test_search_filter(self):
        """
        It should return only two matching projects.
        """
        ProjectFactory.create(name='opdp')
        ProjectFactory.create_batch(2)
        response = self.request(user=self.user, get_data={'search': 'opdp'})
        assert response.status_code == 200
        assert len(response.content['results']) == 1
        assert all([proj['name'] == 'opdp' for proj in
                    response.content['results']])

    def test_ordering(self):
        ProjectFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        response = self.request(user=self.user, get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [proj['name'] for proj in response.content['results']]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        ProjectFactory.create_from_kwargs([
            {'name': 'A'}, {'name': 'C'}, {'name': 'B'}
        ])
        response = self.request(user=self.user, get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [proj['name'] for proj in response.content['results']]
        assert names == sorted(names, reverse=True)

    def test_permission_filter(self):
        addtional_clause = [{
            'effect': 'allow',
            'object': ['project/*/*'],
            'action': ['party.create']
        }, {
            'effect': 'deny',
            'object': ['project/*/unauthorized'],
            'action': ['party.create']
        }]

        ProjectFactory.create_from_kwargs([
            {'slug': 'unauthorized', 'organization': self.organization},
            {'organization': self.organization}
        ])

        assign_policies(self.user, add_clauses=addtional_clause)

        response = self.request(user=self.user,
                                get_data={'permissions': 'party.create'})
        assert response.status_code == 200
        assert len(response.content['results']) == 1
        assert response.content['results'][0]['slug'] != 'unauthorized'

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
        response = self.request(user=user)
        assert response.status_code == 200
        expected_names = [prjs[i].name for i in idxs]
        pnames = [p['name'] for p in response.content['results']]
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


class ProjectCreateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.OrganizationProjectList
    url_kwargs = {'organization': 'habitat'}

    def setup_models(self):
        self.org = OrganizationFactory.create(slug='habitat')
        self.user = UserFactory.create()
        assign_policies(self.user)

    def test_create_valid_project(self):
        data = {
            'name': 'Project',
            'description': 'Project description',
        }
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 201
        assert Project.objects.count() == 1

    def test_create_invalid_project(self):
        data = {
            'description': 'Project description'
        }
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 400
        assert Project.objects.count() == 0
        assert response.content['name'][0] == 'This field is required.'

    def test_create_project_in_archived_organization(self):
        data = {
            'name': 'Project',
            'description': 'Project description',
        }
        self.org.archived = True
        self.org.save()
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert Project.objects.count() == 0


class ProjectDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.ProjectDetail
    post_data = {'name': 'OPDP'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.organization = OrganizationFactory.create(slug='namati')
        self.project = ProjectFactory.create(
            slug='project',
            organization=self.organization,
            name='Test Project',
            archived=False,
            access='public')

        self.oa_group = Group.objects.get(name='OrgAdmin')
        self.om_group = Group.objects.get(name='OrgMember')
        self.pm_group = Group.objects.get(name='ProjectManager')
        OrganizationRole.objects.create(
            organization=self.organization, user=self.user,
            group=self.oa_group)
        ProjectRole.objects.create(
            project=self.project, user=self.user, group=self.pm_group)

    def setup_url_kwargs(self):
        return {
            'organization': self.organization.slug,
            'project': self.project.slug
        }

    def test_get_public_project_with_valid_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.project.id
        assert 'users' in response.content

    def test_get_public_project_with_unauthorized_user(self):
        response = self.request()
        assert response.status_code == 200
        assert response.content['id'] == self.project.id
        assert 'users' not in response.content

    def test_get_public_project_that_does_not_exist(self):
        response = self.request(url_kwargs={'project': 'some-project'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_archived_project_with_unauthorized_user(self):
        self.project.archived = True
        self.project.save()
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_archived_project_with_admin_user(self):
        self.project.archived = True
        self.project.save()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.project.id
        assert 'users' in response.content

    def test_get_private_project(self):
        self.project.access = 'private'
        self.project.save()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.project.id
        assert 'users' in response.content

    def test_get_private_project_with_unauthorized_user(self):
        self.project.access = 'private'
        self.project.save()

        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_private_project_without_permission(self):
        self.project.access = 'private'
        self.project.save()
        user = UserFactory.create()

        response = self.request(user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_private_project_based_on_org_membership(self):
        self.project.access = 'private'
        self.project.save()
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.organization,
                                        user=user, group=self.om_group)

        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.project.id
        assert 'users' in response.content

    def test_get_private_project_with_other_org_membership(self):
        self.project.access = 'private'
        self.project.save()
        user = UserFactory.create()
        other_org = OrganizationFactory.create()
        OrganizationRole.objects.create(
            organization=other_org, user=user, group=self.om_group)

        response = self.request(user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_valid_update(self):
        response = self.request(method='PATCH', user=self.user)
        assert response.status_code == 200
        self.project.refresh_from_db()
        assert self.project.name == 'OPDP'

    def test_PATCH_with_anonymous_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        self.project.refresh_from_db()
        assert self.project.name == 'Test Project'

    def test_PATCH_with_unauthorized_user(self):
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.project.refresh_from_db()
        assert self.project.name == 'Test Project'

    def test_PUT_with_anonymous_user(self):
        response = self.request(method='PUT')
        assert response.status_code == 403
        self.project.refresh_from_db()
        assert self.project.name == 'Test Project'

    def test_PUT_with_unauthorized_user(self):
        response = self.request(method='PUT', user=UserFactory.create())
        assert response.status_code == 403
        self.project.refresh_from_db()
        assert self.project.name == 'Test Project'

    def test_invalid_update(self):
        response = self.request(method='PATCH', user=self.user,
                                post_data={'name': ''})
        assert response.status_code == 400
        self.project.refresh_from_db()
        assert self.project.name == 'Test Project'
        assert self.project.name == 'Test Project'
        assert response.content['name'][0] == "This field may not be blank."

    def test_archive(self):
        response = self.request(method='PATCH', user=self.user,
                                post_data={'archived': True})
        assert response.status_code == 200
        self.project.refresh_from_db()
        assert self.project.archived is True

        response = self.request(method='PATCH', user=self.user,
                                post_data={'description': 'Blah blah blah'})
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert self.project.description != 'Blah blah blah'

    def test_unarchive(self):
        self.project.archived = True
        self.project.save()

        response = self.request(method='PATCH', user=self.user,
                                post_data={'archived': False})
        assert response.status_code == 200
        self.project.refresh_from_db()
        assert self.project.archived is False

    def test_valid_visibility_patching(self):
        # Create users with default list and view permissions for
        # organizations and projects.
        org_user = UserFactory.create()
        non_org_user = UserFactory.create()

        # Create organization, adding just one user.
        org = OrganizationFactory.create(add_users=[org_user])

        # Create public project in organization.
        prj = ProjectFactory.create(
            organization=org, access='public', add_users=[org_user])

        OrganizationRole.objects.create(
            user=self.user, organization=org, group=self.oa_group)

        # User in org SHOULD be able to see project.
        response = self.request(
            user=org_user,
            url_kwargs={'organization': org.slug, 'project': prj.slug})
        assert response.status_code == 200

        # User NOT in org SHOULD be able to see project.
        response = self.request(
            user=non_org_user,
            url_kwargs={'organization': org.slug, 'project': prj.slug})
        assert response.status_code == 200

        # Patch visibility to private.
        response = self.request(
            user=self.user,
            url_kwargs={'organization': org.slug, 'project': prj.slug},
            post_data={'access': 'private'},
            method='PATCH')
        assert response.status_code == 200

        # User in org SHOULD be able to see project.
        response = self.request(
            user=org_user,
            url_kwargs={'organization': org.slug, 'project': prj.slug})
        assert response.status_code == 200

        # User not in org SHOULD NOT be able to see project.
        response = self.request(
            user=non_org_user,
            url_kwargs={'organization': org.slug, 'project': prj.slug})
        assert response.status_code == 403

        # Patch visibility to public.
        response = self.request(
            user=self.user,
            url_kwargs={'organization': org.slug, 'project': prj.slug},
            post_data={'access': 'public'},
            method='PATCH')

        # User in org SHOULD be able to see project.
        response = self.request(
            user=org_user,
            url_kwargs={'organization': org.slug, 'project': prj.slug})
        assert response.status_code == 200
        # User NOT in org SHOULD be able to see project.
        response = self.request(
            user=non_org_user,
            url_kwargs={'organization': org.slug, 'project': prj.slug})
        assert response.status_code == 200

    def test_invalid_visibility_patching(self):
        response = self.request(method='PATCH', user=self.user,
                                post_data={'access': 'something'})
        assert response.status_code == 400
        self.project.refresh_from_db()
        assert self.project.access == 'public'

    def test_delete_fails(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 405
        self.project.refresh_from_db()
        assert Project.objects.filter(id=self.project.id).exists()
