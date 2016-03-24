import json

from django.test import TestCase
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory
from .. import views
from ..models import Organization


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
        assert content['detail'] == 'User with given username does not exist.'

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
