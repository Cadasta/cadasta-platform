import json
from datetime import datetime, timedelta, timezone

from django.test import TestCase
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, ProjectFactory, clause
from .. import views
from ..models import Organization, OrganizationRole, ProjectRole


class OrganizationListAPITest(TestCase):
    def setUp(self):
        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_full_list(self):
        """
        It should return all organizations.
        """
        OrganizationFactory.create_batch(2)
        request = APIRequestFactory().get('/v1/organizations/')
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 2
        assert 'users' not in content[0]

    def test_list_only_one_organization_is_authorized(self):
        """
        It should return all organizations.
        """
        OrganizationFactory.create()
        OrganizationFactory.create(**{'slug': 'unauthorized'})

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*']),
                clause('deny', ['org.view'], ['organization/unauthorized'])
            ]
        }

        policy = Policy.objects.create(
            name='deny',
            body=json.dumps(clauses))
        assign_user_policies(self.user, policy)

        request = APIRequestFactory().get('/v1/organizations/')
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 1
        assert content[0]['slug'] != 'unauthorized'

    def test_full_list_with_unautorized_user(self):
        """
        It should 403 "You do not have permission to perform this action."
        """
        OrganizationFactory.create_batch(2)
        request = APIRequestFactory().get('/v1/organizations/')
        force_authenticate(request, user=AnonymousUser())

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 0

    def test_filter_active(self):
        """
        It should return only one active organization.
        """
        OrganizationFactory.create(**{'archived': True})
        OrganizationFactory.create(**{'archived': False})

        request = APIRequestFactory().get('/v1/organizations/?archived=True')
        setattr(request, 'GET', QueryDict('archived=True'))
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 1

    def test_search_filter(self):
        """
        It should return only two matching organizations.
        """
        OrganizationFactory.create(**{'name': 'A Match'})
        OrganizationFactory.create(**{'description': 'something that matches'})
        OrganizationFactory.create(**{'name': 'Excluded'})

        request = APIRequestFactory().get('/v1/organizations/?search=match')
        setattr(request, 'GET', QueryDict('search=match'))
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 2

        for org in content:
            assert org['name'] != 'Excluded'

    def test_ordering(self):
        OrganizationFactory.create(**{'name': 'A'})
        OrganizationFactory.create(**{'name': 'C'})
        OrganizationFactory.create(**{'name': 'B'})

        request = APIRequestFactory().get('/v1/organizations/?ordering=name')
        setattr(request, 'GET', QueryDict('ordering=name'))
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 3

        prev_name = ''
        for org in content:
            if prev_name:
                assert org['name'] > prev_name

            prev_name = org['name']

    def test_reverse_ordering(self):
        OrganizationFactory.create(**{'name': 'A'})
        OrganizationFactory.create(**{'name': 'C'})
        OrganizationFactory.create(**{'name': 'B'})

        request = APIRequestFactory().get('/v1/organizations/?ordering=-name')
        setattr(request, 'GET', QueryDict('ordering=-name'))
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 3

        prev_name = ''
        for org in content:
            if prev_name:
                assert org['name'] < prev_name

            prev_name = org['name']


class OrganizationCreateAPITest(TestCase):
    def setUp(self):
        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_create_valid_organization(self):
        data = {
            'name': 'Org Name',
            'description': 'Org description'
        }
        request = APIRequestFactory().post('/v1/organizations/', data)
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()

        assert response.status_code == 201
        assert Organization.objects.count() == 1

    def test_create_invalid_organization(self):
        data = {
            'description': 'Org description'
        }
        request = APIRequestFactory().post('/v1/organizations/', data)
        force_authenticate(request, user=self.user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 400
        assert content['name'][0] == 'This field is required.'
        assert Organization.objects.count() == 0

    def test_create_organization_with_unauthorized_user(self):
        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))
        unauthorized_user = UserFactory.create()
        assign_user_policies(unauthorized_user, policy)

        data = {
            'name': 'new_org',
            'description': 'Org description'
        }
        request = APIRequestFactory().post('/v1/organizations/', data)
        force_authenticate(request, user=unauthorized_user)

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert content['detail'] == PermissionDenied.default_detail
        assert Organization.objects.count() == 0


class OrganizationDetailTest(TestCase):
    def setUp(self):
        self.view = views.OrganizationDetail.as_view()

        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_get_organization(self):
        org = OrganizationFactory.create(**{'slug': 'org'})
        request = APIRequestFactory().get(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert content['id'] == org.id
        assert 'users' in content

    def test_get_organization_with_unauthorized_user(self):
        org = OrganizationFactory.create(**{'slug': 'org'})
        request = APIRequestFactory().get(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
        )
        force_authenticate(request, user=AnonymousUser())
        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert content['detail'] == PermissionDenied.default_detail

    def test_get_organization_that_does_not_exist(self):
        request = APIRequestFactory().get('/v1/organizations/some-org/')
        force_authenticate(request, user=self.user)

        response = self.view(request, slug='some-org').render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Organization not found."

    def test_valid_update(self):
        org = OrganizationFactory.create(**{'slug': 'org'})

        data = {'name': 'Org Name'}
        request = APIRequestFactory().patch(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, slug=org.slug).render()
        org.refresh_from_db()

        assert response.status_code == 200
        assert org.name == data.get('name')

    def test_update_with_unauthorized_user(self):
        org = OrganizationFactory.create(**{'name': 'Org name', 'slug': 'org'})

        data = {'name': 'Org Name'}
        request = APIRequestFactory().patch(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=AnonymousUser())

        response = self.view(request, slug=org.slug).render()
        org.refresh_from_db()

        assert response.status_code == 403
        assert org.name == 'Org name'

    def test_invalid_update(self):
        org = OrganizationFactory.create(**{'name': 'Org name', 'slug': 'org'})

        data = {'name': ''}
        request = APIRequestFactory().patch(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))
        org.refresh_from_db()

        assert response.status_code == 400
        assert org.name == 'Org name'
        assert content['name'][0] == 'This field may not be blank.'

    def test_archive(self):
        org = OrganizationFactory.create(**{'name': 'Org name', 'slug': 'org'})

        data = {'archived': True}
        request = APIRequestFactory().patch(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, slug=org.slug).render()
        org.refresh_from_db()

        assert response.status_code == 200
        assert org.archived

    def test_archive_with_unauthorized_user(self):
        org = OrganizationFactory.create(**{'slug': 'org'})

        clauses = {
            'clause': [
                clause('allow', ['org.update'], ['organization/*']),
                clause('deny', ['org.archive'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))
        assign_user_policies(self.user, policy)

        data = {'archived': True}
        request = APIRequestFactory().patch(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, slug=org.slug).render()
        org.refresh_from_db()

        assert response.status_code == 403
        assert not org.archived

    def test_unarchive(self):
        org = OrganizationFactory.create(**{'slug': 'org', 'archived': True})

        data = {'archived': False}
        request = APIRequestFactory().patch(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, slug=org.slug).render()
        org.refresh_from_db()

        assert response.status_code == 200
        assert not org.archived

    def test_unarchive_unauthorized_user(self):
        org = OrganizationFactory.create(**{'slug': 'org', 'archived': True})

        clauses = {
            'clause': [
                clause('allow', ['org.update'], ['organization/*']),
                clause('deny', ['org.unarchive'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))
        assign_user_policies(self.user, policy)

        data = {'archived': False}
        request = APIRequestFactory().patch(
            '/v1/organizations/{slug}/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, slug=org.slug).render()
        org.refresh_from_db()

        assert response.status_code == 403
        assert org.archived


class OrganizationUsersTest(TestCase):
    def setUp(self):
        self.view = views.OrganizationUsers.as_view()

        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_get_users(self):
        org_users = UserFactory.create_batch(2)
        other_user = UserFactory.create()

        org = OrganizationFactory.create(add_users=org_users)
        request = APIRequestFactory().get(
            '/v1/organizations/{slug}/users/'.format(slug=org.slug)
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 2
        assert other_user.username not in [u['username'] for u in content]

    def test_get_users_with_unauthorized_user(self):
        org = OrganizationFactory.create()
        request = APIRequestFactory().get(
            '/v1/organizations/{slug}/users/'.format(slug=org.slug)
        )
        force_authenticate(request, user=AnonymousUser())
        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert content['detail'] == PermissionDenied.default_detail

    def test_add_user(self):
        org_users = UserFactory.create_batch(2)
        new_user = UserFactory.create()
        data = {'username': new_user.username}

        org = OrganizationFactory.create(add_users=org_users)
        request = APIRequestFactory().post(
            '/v1/organizations/{slug}/users/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, slug=org.slug).render()

        assert response.status_code == 201
        assert org.users.count() == 3

    def test_add_user_with_unauthorized_user(self):
        org_users = UserFactory.create_batch(2)
        new_user = UserFactory.create()
        data = {'username': new_user.username}

        org = OrganizationFactory.create(add_users=org_users)
        request = APIRequestFactory().post(
            '/v1/organizations/{slug}/users/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=AnonymousUser())
        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert content['detail'] == PermissionDenied.default_detail
        assert org.users.count() == 2

    def test_add_user_that_does_not_exist(self):
        org_users = UserFactory.create_batch(2)
        data = {'username': 'some_username'}

        org = OrganizationFactory.create(add_users=org_users)
        request = APIRequestFactory().post(
            '/v1/organizations/{slug}/users/'.format(slug=org.slug),
            data
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, slug=org.slug).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 400
        assert org.users.count() == 2
        assert ('User with username or email some_username does not exist'
                in content['username'])

    def test_add_user_to_organization_that_does_not_exist(self):
        new_user = UserFactory.create()
        data = {'username': new_user.username}

        request = APIRequestFactory().post(
            '/v1/organizations/some-org/users/',
            data
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, slug='some-org').render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Organization not found."


class OrganizationUsersDetailTest(TestCase):
    def setUp(self):
        self.view = views.OrganizationUsersDetail.as_view()

        clauses = {
            'clause': [
                clause('allow', ['org.*']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_get_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])

        request = APIRequestFactory().get(
            '/v1/organizations/{org}/users/{username}'.format(
                org=org.slug,
                username=user.username)
        )
        force_authenticate(request, user=self.user)
        response = self.view(
            request,
            slug=org.slug,
            username=user.username).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert content['username'] == user.username

    def test_update_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])

        request = APIRequestFactory().patch(
            '/v1/organizations/{org}/users/{username}'.format(
                org=org.slug,
                username=user.username),
            data={
                'roles': {
                    'admin': True
                }
            },
            format='json'
        )
        force_authenticate(request, user=self.user)
        response = self.view(
            request,
            slug=org.slug,
            username=user.username).render()
        assert response.status_code == 200
        assert org.users.count() == 1

        role = OrganizationRole.objects.get(organization=org, user=user)
        assert role.admin is True

    def test_remove_user(self):
        user = UserFactory.create()
        user_to_remove = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user, user_to_remove])

        request = APIRequestFactory().delete(
            '/v1/organizations/{org}/users/{username}'.format(
                org=org.slug,
                username=user_to_remove.username)
        )
        force_authenticate(request, user=self.user)
        response = self.view(
            request,
            slug=org.slug,
            username=user_to_remove.username).render()
        assert response.status_code == 204
        assert org.users.count() == 1
        assert user_to_remove not in org.users.all()

    def test_remove_with_unauthorized_user(self):
        user = UserFactory.create()
        user_to_remove = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user, user_to_remove])

        request = APIRequestFactory().delete(
            '/v1/organizations/{org}/users/{username}'.format(
                org=org.slug,
                username=user_to_remove.username)
        )
        force_authenticate(request, user=AnonymousUser())
        response = self.view(
            request,
            slug=org.slug,
            username=user_to_remove.username).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert org.users.count() == 2
        assert content['detail'] == PermissionDenied.default_detail

    def test_remove_user_that_does_not_exist(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])

        request = APIRequestFactory().delete(
            '/v1/organizations/{org}/users/{username}'.format(
                org=org.slug,
                username='some_username')
        )
        force_authenticate(request, user=self.user)
        response = self.view(
            request,
            slug=org.slug,
            username='some_username').render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert org.users.count() == 1
        assert content['detail'] == "User not found."

    def test_remove_user_from_organization_that_does_not_exist(self):
        user = UserFactory.create()

        request = APIRequestFactory().delete(
            '/v1/organizations/{org}/users/{username}'.format(
                org='some-org',
                username=user.username)
        )
        force_authenticate(request, user=self.user)
        response = self.view(
            request,
            slug='some-org',
            username=user.username).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Organization not found."


# class ProjectListAPITest(TestCase):
#     def setUp(self):
#         clause = {
#             'clause': [
#                 {
#                   'effect': 'allow',
#                   'object': ['organization/*'],
#                   'action': ['project.list']
#                 }
#             ]
#         }

#         policy = Policy.objects.create(
#             name='default',
#             body=json.dumps(clause))
#         self.user = UserFactory.create()
#         assign_user_policies(self.user, policy)

#     def test_full_list(self):
#         """
#         It should return all organizations.
#         """
#         organization = OrganizationFactory.create(**{'slug': 'habitat'})
#         ProjectFactory.create_batch(2, **{'organization': organization})
#         ProjectFactory.create_batch(2)
#         request = APIRequestFactory().get('/v1/organizations/habitat/projects/')
#         force_authenticate(request, user=self.user)

#         response = views.ProjectList.as_view()(request).render()
#         content = json.loads(response.content.decode('utf-8'))

#         assert response.status_code == 200
#         assert len(content) == 2

#         for project in content:
#             assert project.get('organization').get('id') == organization.id

#     def test_create_valid_project(self):
#         data = {
#             'name': 'Project Name',
#             'description': 'Project description'
#         }
#         organization = OrganizationFactory.create(**{'slug': 'habitat'})
#         request = APIRequestFactory().post('/v1/organizations/habitat/projects/', data)
#         force_authenticate(request, user=self.user)

#         response = views.ProjectList.as_view()(request).render()

#         assert response.status_code == 201
#         assert organization.projects.count() == 1


class ProjectUsersAPITest(TestCase):
    def setUp(self):
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

        self.view = views.ProjectUsers.as_view()

    def _get(self, org, prj, user=AnonymousUser()):
        request = APIRequestFactory().get(
            '/v1/organizations/{org}/projects/{prj}/users/'.format(
                org=org,
                prj=prj
            )
        )
        force_authenticate(request, user=user)
        return self.view(request, slug=org, project_id=prj).render()

    def _post(self, org, prj, data={}, user=AnonymousUser()):
        request = APIRequestFactory().post(
            '/v1/organizations/{org}/projects/{prj}/users/'.format(
                org=org,
                prj=prj
            ),
            data,
            format='json'
        )
        force_authenticate(request, user=user)

        return self.view(request, slug=org, project_id=prj).render()

    def test_full_list(self):
        """
        It should return all organizations.
        """
        prj_users = UserFactory.create_batch(2)
        other_user = UserFactory.create()

        project = ProjectFactory.create(add_users=prj_users)
        response = self._get(
            org=project.organization.slug,
            prj=project.id,
            user=self.user
        )
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 2
        assert other_user.username not in [u['username'] for u in content]

    def test_full_list_with_unauthorized_user(self):
        project = ProjectFactory.create()
        response = self._get(
            org=project.organization.slug,
            prj=project.id
        )

        assert response.status_code == 403

    def test_get_full_list_organization_does_not_exist(self):
        project = ProjectFactory.create()
        response = self._get(
            org='some-org',
            prj=project.id,
            user=self.user
        )
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        organization = OrganizationFactory.create()
        response = self._get(
            org=organization.slug,
            prj='123abd',
            user=self.user
        )
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Project not found."

    def test_add_user(self):
        user_to_add = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user_to_add])
        project = ProjectFactory.create(**{'organization': org})
        response = self._post(
            org=project.organization.slug,
            prj=project.id,
            user=self.user,
            data={'username': user_to_add.username}
        )

        assert response.status_code == 201
        assert project.users.count() == 1

    def test_add_user_with_unauthorized_user(self):
        user_to_add = UserFactory.create()
        project = ProjectFactory.create()
        response = self._post(
            org=project.organization.slug,
            prj=project.id,
            data={'username': user_to_add.username}
        )

        assert response.status_code == 403
        assert project.users.count() == 0

    def test_add_user_with_invalid_data(self):
        project = ProjectFactory.create()
        response = self._post(
            org=project.organization.slug,
            prj=project.id,
            user=self.user,
            data={'username': 'some-user'}
        )
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 400
        assert project.users.count() == 0
        assert ('User with username or email some-user does not exist'
                in content['username'])


class ProjectUsersDetailTest(TestCase):
    def setUp(self):
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

        self.view = views.ProjectUsersDetail.as_view()

    def _get(self, org, prj, user, auth=AnonymousUser()):
        request = APIRequestFactory().get(
            '/v1/organizations/{org}/projects/{prj}/users/{user}'.format(
                org=org,
                prj=prj,
                user=user
            )
        )
        force_authenticate(request, user=auth)
        return self.view(
            request, slug=org, project_id=prj, username=user).render()

    def _patch(self, org, prj, user, data, auth=AnonymousUser()):
        request = APIRequestFactory().patch(
            '/v1/organizations/{org}/projects/{prj}/users/{user}'.format(
                org=org,
                prj=prj,
                user=user
            ),
            data,
            format='json'
        )
        force_authenticate(request, user=auth)
        return self.view(
            request, slug=org, project_id=prj, username=user).render()

    def _delete(self, org, prj, user, auth=AnonymousUser()):
        request = APIRequestFactory().delete(
            '/v1/organizations/{org}/projects/{prj}/users/{user}'.format(
                org=org,
                prj=prj,
                user=user
            )
        )
        force_authenticate(request, user=auth)
        return self.view(
            request, slug=org, project_id=prj, username=user).render()

    def test_get_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        response = self._get(
            org=project.organization.slug,
            prj=project.id,
            user=user.username,
            auth=self.user)
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert content['username'] == user.username

    def test_get_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        response = self._get(
            org=project.organization.slug,
            prj=project.id,
            user=user.username)

        assert response.status_code == 403

    def test_get_user_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        response = self._get(
            org=project.organization.slug,
            prj=project.id,
            user=user.username,
            auth=self.user)
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "User not found."

    def test_get_user_from_org_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        response = self._get(
            org='some-org',
            prj=project.id,
            user=user.username,
            auth=self.user)
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Project not found."

    def test_get_user_from_project_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        response = self._get(
            org=project.organization.slug,
            prj='abc123',
            user=user.username,
            auth=self.user)
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Project not found."

    def test_update_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        data = {
            'roles': {
                'manager': True
            }
        }

        response = self._patch(
            org=project.organization.slug,
            prj=project.id,
            user=user.username,
            data=data,
            auth=self.user)

        assert response.status_code == 200
        role = ProjectRole.objects.get(project=project, user=user)
        assert role.manager is True

    def test_update_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        data = {
            'roles': {
                'manager': True
            }
        }

        response = self._patch(
            org=project.organization.slug,
            prj=project.id,
            user=user.username,
            data=data)

        assert response.status_code == 403
        role = ProjectRole.objects.get(project=project, user=user)
        assert role.manager is False

    def test_delete_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        response = self._delete(
            org=project.organization.slug,
            prj=project.id,
            user=user.username,
            auth=self.user)

        assert response.status_code == 204
        assert project.users.count() == 0

    def test_delete_user_with_unauthorized_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        response = self._delete(
            org=project.organization.slug,
            prj=project.id,
            user=user.username)

        assert response.status_code == 403
        assert project.users.count() == 1


class UserListAPITest(TestCase):
    def setUp(self):
        clauses = {
            'clause': [
                clause('allow', ['user.view'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_full_list(self):
        """
        It should return all users.
        """
        UserFactory.create_batch(2)
        request = APIRequestFactory().get('/v1/users/')
        force_authenticate(request, user=self.user)

        response = views.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 3

    def test_full_list_organizations(self):
        """
        It should return all users with their organizations.
        """
        user1, user2 = UserFactory.create_batch(2)
        o0 = OrganizationFactory.create(add_users=[user1, user2])
        o1 = OrganizationFactory.create(add_users=[user1])
        o2 = OrganizationFactory.create(add_users=[user2])
        request = APIRequestFactory().get('/v1/users/')
        force_authenticate(request, user=self.user)

        response = views.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 3
        assert 'organizations' in content[0]
        assert content[0]['organizations'] == []
        assert 'organizations' in content[1]
        assert {'id': o0.id, 'name': o0.name} in content[1]['organizations']
        assert {'id': o1.id, 'name': o1.name} in content[1]['organizations']
        assert 'organizations' in content[2]
        assert {'id': o0.id, 'name': o0.name} in content[2]['organizations']
        assert {'id': o2.id, 'name': o2.name} in content[2]['organizations']

    def test_full_list_with_unautorized_user(self):
        """
        It should 403 "You do not have permission to perform this action."
        """
        UserFactory.create_batch(2)
        request = APIRequestFactory().get('/v1/users/')
        force_authenticate(request, user=AnonymousUser())

        response = views.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert content['detail'] == PermissionDenied.default_detail

    def test_filter_active(self):
        """
        It should return only one active user (plus the "setup" user).
        """
        UserFactory.create(**{'is_active': True})
        UserFactory.create(**{'is_active': False})

        request = APIRequestFactory().get('/v1/users/?is_active=True')
        setattr(request, 'GET', QueryDict('is_active=True'))
        force_authenticate(request, user=self.user)

        response = views.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 2

    def test_search_filter(self):
        """
        It should return only two matching users.
        """
        UserFactory.create(**{'last_name': 'Match'})
        UserFactory.create(**{'username': 'ivegotamatch'})
        UserFactory.create(**{'username': 'excluded'})

        request = APIRequestFactory().get('/v1/users/?search=match')
        setattr(request, 'GET', QueryDict('search=match'))
        force_authenticate(request, user=self.user)

        response = views.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 2

        for user in content:
            assert user['username'] != 'excluded'

    def test_ordering(self):
        UserFactory.create(**{'username': 'A'})
        UserFactory.create(**{'username': 'C'})
        UserFactory.create(**{'username': 'B'})

        request = APIRequestFactory().get('/v1/users/?ordering=username')
        setattr(request, 'GET', QueryDict('ordering=username'))
        force_authenticate(request, user=self.user)

        response = views.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 4

        prev_username = ''
        for user in content:
            if prev_username:
                assert user['username'] > prev_username

            prev_username = user['username']

    def test_reverse_ordering(self):
        UserFactory.create(**{'username': 'A'})
        UserFactory.create(**{'username': 'C'})
        UserFactory.create(**{'username': 'B'})

        request = APIRequestFactory().get('/v1/users/?ordering=-username')
        setattr(request, 'GET', QueryDict('ordering=-username'))
        force_authenticate(request, user=self.user)

        response = views.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 4

        prev_username = ''
        for org in content:
            if prev_username:
                assert org['username'] < prev_username

            prev_username = org['username']


class UserDetailAPITest(TestCase):
    def setUp(self):
        self.view = views.UserAdminDetail.as_view()

        clauses = {
            'clause': [
                clause('allow', ['user.*']),
                clause('allow', ['user.*'], ['user/*'])
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))

        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_get_user(self):
        user = UserFactory.create(**{'username': 'test-user'})
        request = APIRequestFactory().get(
            '/v1/users/{username}/'.format(username=user.username),
        )
        force_authenticate(request, user=self.user)
        response = self.view(request, username=user.username).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert content['username'] == user.username
        assert 'organizations' in content

    def test_get_user_with_unauthorized_user(self):
        user = UserFactory.create(**{'username': 'test-user'})
        request = APIRequestFactory().get(
            '/v1/users/{username}/'.format(username=user.username),
        )
        force_authenticate(request, user=AnonymousUser())
        response = self.view(request, username=user.username).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert content['detail'] == PermissionDenied.default_detail

    def test_get_user_that_does_not_exist(self):
        request = APIRequestFactory().get('/v1/users/some-user/')
        force_authenticate(request, user=self.user)

        response = self.view(request, username='some-user').render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "User not found."

    def test_valid_update(self):
        user = UserFactory.create(**{'username': 'test-user'})
        assert user.is_active

        data = {'is_active': False}
        request = APIRequestFactory().patch(
            '/v1/users/{username}/'.format(username=user.username),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, username=user.username).render()
        user.refresh_from_db()

        assert response.status_code == 200
        assert user.is_active == data.get('is_active')

    def test_update_with_unauthorized_user(self):
        user = UserFactory.create(**{'last_name': 'Smith',
                                     'username': 'test-user'})

        data = {'last_name': 'Jones'}
        request = APIRequestFactory().patch(
            '/v1/users/{username}/'.format(username=user.username),
            data
        )
        force_authenticate(request, user=AnonymousUser())

        response = self.view(request, username=user.username).render()
        user.refresh_from_db()

        assert response.status_code == 403
        assert user.last_name == 'Smith'

    def test_invalid_update(self):
        t1 = datetime(12, 10, 30, tzinfo=timezone.utc)
        t2 = t1 + timedelta(seconds=10)
        user = UserFactory.create(**{'last_login': t1,
                                     'username': 'test-user'})

        data = {'last_login': t2}
        request = APIRequestFactory().patch(
            '/v1/users/{username}/'.format(username=user.username),
            data
        )
        force_authenticate(request, user=self.user)

        response = self.view(request, username=user.username).render()
        content = json.loads(response.content.decode('utf-8'))
        user.refresh_from_db()

        assert response.status_code == 400
        assert user.last_login == t1
        assert content['last_login'][0] == 'Cannot update last_login'
