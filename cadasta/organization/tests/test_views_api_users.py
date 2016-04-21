import json
from datetime import datetime, timedelta, timezone

from django.test import TestCase
from django.utils.translation import gettext as _
from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, clause
from ..views import api


class UserListAPITest(TestCase):
    def setUp(self):
        clauses = {
            'clause': [
                clause('allow', ['user.list'])
            ]
        }
        policy = Policy.objects.create(
            name='default',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)

    def _get(self, user=None, query=None, status=None, length=None):
        if user is None:
            user = self.user
        url = '/v1/users/'
        if query is not None:
            url += '?' + query
        request = APIRequestFactory().get(url)
        if query is not None:
            setattr(request, 'GET', QueryDict(query))
        force_authenticate(request, user=user)
        response = api.UserAdminList.as_view()(request).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content) == length
        return content

    def test_full_list(self):
        """
        It should return all users.
        """
        UserFactory.create_batch(2)
        self._get(status=200, length=3)

    def test_full_list_organizations(self):
        """
        It should return all users with their organizations.
        """
        user1, user2 = UserFactory.create_batch(2)
        o0 = OrganizationFactory.create(add_users=[user1, user2])
        o1 = OrganizationFactory.create(add_users=[user1])
        o2 = OrganizationFactory.create(add_users=[user2])
        content = self._get(status=200, length=3)
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
        content = self._get(user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_filter_active(self):
        """
        It should return only one active user (plus the "setup" user).
        """
        UserFactory.create_from_kwargs([
            {'is_active': True}, {'is_active': False}
        ])
        self._get(query='is_active=True', status=200, length=2)

    def test_search_filter(self):
        """
        It should return only two matching users.
        """
        UserFactory.create_from_kwargs([
            {'last_name': 'Match'},
            {'username': 'ivegotamatch'},
            {'username': 'excluded'}
        ])
        content = self._get(query='search=match', status=200, length=2)
        assert not any([user['username'] == 'excluded' for user in content])

    def test_ordering(self):
        UserFactory.create_from_kwargs([
            {'username': 'A'}, {'username': 'C'}, {'username': 'B'}
        ])
        content = self._get(query='ordering=username', status=200, length=4)
        usernames = [user['username'] for user in content]
        assert(usernames == sorted(usernames))

    def test_reverse_ordering(self):
        UserFactory.create_from_kwargs([
            {'username': 'A'}, {'username': 'C'}, {'username': 'B'}
        ])
        content = self._get(query='ordering=-username', status=200, length=4)
        usernames = [user['username'] for user in content]
        assert(usernames == sorted(usernames, reverse=True))


class UserDetailAPITest(TestCase):
    def setUp(self):
        self.view = api.UserAdminDetail.as_view()

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

    def _get(self, username, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/users/{username}/'
        request = APIRequestFactory().get(url.format(username=username))
        force_authenticate(request, user=user)
        response = self.view(request, username=username).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, username, data, user=None, status=None):
        if user is None:
            user = self.user
        url = '/v1/users/{username}/'
        request = APIRequestFactory().patch(url.format(username=username),
                                            data)
        force_authenticate(request, user=user)
        response = self.view(request, username=username).render()
        content = None
        if len(response.content) > 0:
            content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def test_get_user(self):
        user = UserFactory.create(username='test-user')
        content = self._get(user.username, status=200)
        assert content['username'] == user.username
        assert 'organizations' in content

    def test_get_user_with_unauthorized_user(self):
        user = UserFactory.create(username='test-user')
        content = self._get(user.username, user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_get_user_that_does_not_exist(self):
        content = self._get('some-user', status=404)
        assert content['detail'] == "User not found."

    def test_valid_update(self):
        user = UserFactory.create(username='test-user')
        assert user.is_active
        data = {'is_active': False}
        self._patch(user.username, data, status=200)
        user.refresh_from_db()
        assert user.is_active == data.get('is_active')

    def test_update_with_unauthorized_user(self):
        user = UserFactory.create(last_name='Smith', username='test-user')
        self._patch(user.username, {'last_name': 'Jones'},
                    user=AnonymousUser(), status=403)
        user.refresh_from_db()
        assert user.last_name == 'Smith'

    def test_invalid_update(self):
        t1 = datetime(12, 10, 30, tzinfo=timezone.utc)
        t2 = t1 + timedelta(seconds=10)
        user = UserFactory.create(last_login=t1, username='test-user')
        content = self._patch(user.username, {'last_login': t2}, status=400)
        user.refresh_from_db()
        assert user.last_login == t1
        assert content['last_login'][0] == _('Cannot update last_login')
