import json

from django.test import TestCase
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, ProjectFactory
from .. import views
from ..models import Organization, OrganizationRole, ProjectRole


class OrganizationListAPITest(TestCase):
    def setUp(self):
        clause = {
            'clause': [
                {
                  'effect': 'allow',
                  'object': ['*'],
                  'action': ['org.list']
                }, {
                  'effect': 'allow',
                  'object': ['organization/*'],
                  'action': ['org.view']
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
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

    # def test_list_only_one_organization_is_authorized(self):
    #     """
    #     It should return all organizations.
    #     """
    #     OrganizationFactory.create()
    #     OrganizationFactory.create(**{'slug': 'unauthorized'})

    #     clause = {
    #         'clause': [{
    #             "effect": "allow",
    #             "object": ["*"],
    #             "action": ["org.list"]
    #         }, {
    #             "effect": "allow",
    #             "object": ["organization/*"],
    #             "action": ["org.view"]
    #         }, {
    #             'effect': 'deny',
    #             'object': ['organization/unauthorized'],
    #             'action': ['org.view']
    #         }]
    #     }

    #     policy = Policy.objects.create(
    #         name='deny',
    #         body=json.dumps(clause))
    #     assign_user_policies(self.user, policy)

    #     request = APIRequestFactory().get('/v1/organizations/')
    #     force_authenticate(request, user=self.user)

    #     response = views.OrganizationList.as_view()(request).render()
    #     content = json.loads(response.content.decode('utf-8'))

    #     assert response.status_code == 200
    #     assert len(content) == 1
    #     assert content[0]['slug'] != 'unauthorized'

    def test_full_list_with_unautorized_user(self):
        """
        It should 403 "You do not have permission to perform this action."
        """
        OrganizationFactory.create_batch(2)
        request = APIRequestFactory().get('/v1/organizations/')
        force_authenticate(request, user=AnonymousUser())

        response = views.OrganizationList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 403
        assert content['detail'] == PermissionDenied.default_detail

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
        clause = {
            "clause": [
                {
                      "effect": "allow",
                      "object": ["*"],
                      "action": ["org.*"]
                }, {
                      "effect": "allow",
                      "object": ["organization/*"],
                      "action": ["org.*"]
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))

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
        clause = {
            'clause': [
                {
                  'effect': 'allow',
                  'object': ['*'],
                  'action': ['org.list']
                }, {
                  'effect': 'allow',
                  'object': ['organization/*'],
                  'action': ['org.view']
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
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

        clause = {
            "clause": [
                {
                      "effect": "allow",
                      "object": ["*"],
                      "action": ["org.*"]
                }, {
                      "effect": "allow",
                      "object": ["organization/*"],
                      "action": ["org.*"]
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))

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

        clause = {
            "clause": [
                {
                      "effect": "allow",
                      "object": ["organization/*"],
                      "action": ["org.update"]
                }, {
                      "effect": "deny",
                      "object": ["organization/*"],
                      "action": ["org.archive"]
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
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

        clause = {
            "clause": [
                {
                      "effect": "allow",
                      "object": ["organization/*"],
                      "action": ["org.update"]
                }, {
                      "effect": "deny",
                      "object": ["organization/*"],
                      "action": ["org.unarchive"]
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
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

        clause = {
            "clause": [
                {
                      "effect": "allow",
                      "object": ["*"],
                      "action": ["org.*"]
                }, {
                      "effect": "allow",
                      "object": ["organization/*"],
                      "action": ["org.*", "org.*.*"]
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))

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
        assert 'User some_username does not exist' in content['username']

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

        clause = {
            "clause": [
                {
                      "effect": "allow",
                      "object": ["*"],
                      "action": ["org.*"]
                }, {
                      "effect": "allow",
                      "object": ["organization/*"],
                      "action": ["org.*", "org.*.*"]
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))

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
                  'effect': 'allow',
                  'object': ['organization/*'],
                  'action': ['org.*']
                }, {
                  'effect': 'allow',
                  'object': ['project/*/*'],
                  'action': ['project.*.*']
                }
            ]
        }

        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

        self.view = views.ProjectUsers.as_view()

    def test_full_list(self):
        """
        It should return all organizations.
        """
        prj_users = UserFactory.create_batch(2)
        other_user = UserFactory.create()

        project = ProjectFactory.create(add_users=prj_users)
        request = APIRequestFactory().get(
            '/v1/organizations/{org}/projects/{prj}/users/'.format(
                org=project.organization.slug,
                prj=project.id
            )
        )
        # request.user = self.user
        # request.successful_authenticator = True
        force_authenticate(request, user=self.user)

        response = self.view(
            request,
            slug=project.organization.slug,
            project_id=project.id).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert len(content) == 2
        assert other_user.username not in [u['username'] for u in content]

    def test_full_list_with_unauthorized_user(self):
        pass

    def test_get_full_list_organization_does_not_exist(self):
        project = ProjectFactory.create()
        request = APIRequestFactory().get(
            '/v1/organizations/some-org/projects/{prj}/users/'.format(
                prj=project.id
            )
        )
        response = self.view(
            request,
            slug='some-org',
            project_id=project.id).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        organization = OrganizationFactory.create()
        request = APIRequestFactory().get(
            '/v1/organizations/{slug}/projects/{prj}/users/'.format(
                slug=organization.slug,
                prj='123abd'
            )
        )
        response = self.view(
            request,
            slug=organization.slug,
            project_id='123abc').render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Project not found."

    def test_add_user(self):
        user_to_add = UserFactory.create()
        project = ProjectFactory.create()
        request = APIRequestFactory().post(
            '/v1/organizations/{org}/projects/{prj}/users/'.format(
                org=project.organization.slug,
                prj=project.id
            ),
            {'username': user_to_add.username}
        )
        force_authenticate(request, user=self.user)

        response = self.view(
            request,
            slug=project.organization.slug,
            project_id=project.id).render()

        assert response.status_code == 201
        assert project.users.count() == 1

    def test_add_user_with_invalid_data(self):
        project = ProjectFactory.create()
        request = APIRequestFactory().post(
            '/v1/organizations/{org}/projects/{prj}/users/'.format(
                org=project.organization.slug,
                prj=project.id
            ),
            {'username': 'some-user'}
        )
        force_authenticate(request, user=self.user)

        response = self.view(
            request,
            slug=project.organization.slug,
            project_id=project.id).render()
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 400
        assert project.users.count() == 0
        assert 'User some-user does not exist' in content['username']


class ProjectUsersDetailTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.view = views.ProjectUsersDetail.as_view()

    def _get(self, org, prj, user):
        request = APIRequestFactory().get(
            '/v1/organizations/{org}/projects/{prj}/users/{user}'.format(
                org=org,
                prj=prj,
                user=user
            )
        )
        force_authenticate(request, user=self.user)
        return self.view(
            request, slug=org, project_id=prj, username=user).render()

    def _patch(self, org, prj, user, data):
        request = APIRequestFactory().patch(
            '/v1/organizations/{org}/projects/{prj}/users/{user}'.format(
                org=org,
                prj=prj,
                user=user
            ),
            data,
            format='json'
        )
        force_authenticate(request, user=self.user)
        return self.view(
            request, slug=org, project_id=prj, username=user).render()

    def _delete(self, org, prj, user):
        request = APIRequestFactory().delete(
            '/v1/organizations/{org}/projects/{prj}/users/{user}'.format(
                org=org,
                prj=prj,
                user=user
            )
        )
        force_authenticate(request, user=self.user)
        return self.view(
            request, slug=org, project_id=prj, username=user).render()

    def test_get_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        response = self._get(
            org=project.organization.slug,
            prj=project.id,
            user=user.username)
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 200
        assert content['username'] == user.username

    def test_get_user_with_unauthorized_user(self):
        pass

    def test_get_user_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        response = self._get(
            org=project.organization.slug,
            prj=project.id,
            user=user.username)
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "User not found."

    def test_get_user_from_org_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        response = self._get(
            org='some-org',
            prj=project.id,
            user=user.username)
        content = json.loads(response.content.decode('utf-8'))

        assert response.status_code == 404
        assert content['detail'] == "Project not found."

    def test_get_user_from_project_that_does_not_exist(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        response = self._get(
            org=project.organization.slug,
            prj='abc123',
            user=user.username)
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
            data=data)

        assert response.status_code == 200
        role = ProjectRole.objects.get(project=project, user=user)
        assert role.manager is True

    def test_update_user_with_unauthorized_user(self):
        pass

    def test_delete_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        response = self._delete(
            org=project.organization.slug,
            prj=project.id,
            user=user.username)

        assert response.status_code == 204
        assert project.users.count() == 0

    def test_delete_user_with_unauthorized_user(self):
        pass
