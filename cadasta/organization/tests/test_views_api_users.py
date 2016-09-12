import json
from datetime import datetime, timedelta, timezone

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, clause
from ..views.api import UserAdminList, UserAdminDetail


class UserListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = UserAdminList

    def setup_models(self):
        clauses = {
            'clause': [
                clause('allow', ['user.list'])
            ]
        }
        policy = Policy.objects.create(
            name='test-default',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def test_full_list(self):
        """
        It should return all users.
        """
        UserFactory.create_batch(2)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content) == 3

    def test_full_list_organizations(self):
        """
        It should return all users with their organizations.
        """
        user1, user2 = UserFactory.create_batch(2)
        o0 = OrganizationFactory.create(add_users=[user1, user2])
        o1 = OrganizationFactory.create(add_users=[user1])
        o2 = OrganizationFactory.create(add_users=[user2])
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content) == 3

        assert 'organizations' in response.content[0]
        assert response.content[0]['organizations'] == []
        assert 'organizations' in response.content[1]
        assert ({'id': o0.id, 'name': o0.name}
                in response.content[1]['organizations'])
        assert ({'id': o1.id, 'name': o1.name}
                in response.content[1]['organizations'])
        assert 'organizations' in response.content[2]
        assert ({'id': o0.id, 'name': o0.name}
                in response.content[2]['organizations'])
        assert ({'id': o2.id, 'name': o2.name}
                in response.content[2]['organizations'])

    def test_full_list_with_unautorized_user(self):
        """
        It should 403 "You do not have permission to perform this action."
        """
        UserFactory.create_batch(2)
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_filter_active(self):
        """
        It should return only one active user (plus the "setup" user).
        """
        UserFactory.create_from_kwargs([
            {'is_active': True}, {'is_active': False}
        ])
        response = self.request(user=self.user, get_data={'is_active': True})
        assert response.status_code == 200
        assert len(response.content) == 2

    def test_search_filter(self):
        """
        It should return only two matching users.
        """
        UserFactory.create_from_kwargs([
            {'full_name': 'Match'},
            {'username': 'ivegotamatch'},
            {'username': 'excluded'}
        ])
        response = self.request(user=self.user, get_data={'search': 'match'})
        assert response.status_code == 200
        assert len(response.content) == 2
        assert not any([user['username'] == 'excluded'
                        for user in response.content])

    def test_ordering(self):
        UserFactory.create_from_kwargs([
            {'username': 'A'}, {'username': 'C'}, {'username': 'B'}
        ])
        response = self.request(user=self.user,
                                get_data={'ordering': 'username'})
        assert response.status_code == 200
        assert len(response.content) == 4
        usernames = [user['username'] for user in response.content]
        assert(usernames == sorted(usernames))

    def test_reverse_ordering(self):
        UserFactory.create_from_kwargs([
            {'username': 'A'}, {'username': 'C'}, {'username': 'B'}
        ])
        response = self.request(user=self.user,
                                get_data={'ordering': '-username'})
        assert response.status_code == 200
        assert len(response.content) == 4
        usernames = [user['username'] for user in response.content]
        assert(usernames == sorted(usernames, reverse=True))


class UserDetailAPITest(APITestCase, TestCase):
    view_class = UserAdminDetail

    def setup_models(self):
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
        self.test_user = UserFactory.create(username='test-user')

    def setup_url_kwargs(self):
        return {'username': self.test_user.username}

    def test_get_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['username'] == self.test_user.username
        assert 'organizations' in response.content

    def test_get_user_with_unauthorized_user(self):
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_user_that_does_not_exist(self):
        response = self.request(user=self.user, url_kwargs={'username': 'som'})
        assert response.status_code == 404
        assert response.content['detail'] == "User not found."

    def test_valid_update(self):
        data = {'is_active': False}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 200
        self.test_user.refresh_from_db()
        assert self.test_user.is_active == data.get('is_active')

    def test_update_with_unauthorized_user(self):
        data = {'full_name': 'Jones'}
        response = self.request(method='PATCH', post_data=data)
        assert response.status_code == 403
        self.test_user.refresh_from_db()
        assert self.test_user.full_name != 'Jones'

    def test_invalid_update(self):
        t1 = datetime(12, 10, 30, tzinfo=timezone.utc)
        t2 = t1 + timedelta(seconds=10)
        self.test_user.last_login = t1
        self.test_user.save()
        data = {'last_login': str(t2)}

        response = self.request(method='PATCH', post_data=data, user=self.user)
        assert response.status_code == 400
        assert response.content['last_login'][0] == "Cannot update last_login"
        self.test_user.refresh_from_db()
        assert self.test_user.last_login == t1
