import json
from django.test import TestCase
from django.http import HttpRequest, Http404
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
import pytest

from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory
from ..views import default
from .factories import clause


USER_CLAUSES = {
    'clause': [
        clause('allow', ['user.list']),
        clause('allow', ['user.update'], ['user/*'])
    ]
}


class UserListTest(TestCase):
    def setUp(self):
        self.view = default.UserList.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.u1 = UserFactory.create()
        self.u2 = UserFactory.create()
        self.u3 = UserFactory.create()
        self.org1 = OrganizationFactory.create(name='A', add_users=[self.u1])
        self.org2 = OrganizationFactory.create(
            name='B', add_users=[self.u1, self.u2]
        )

        self.policy = Policy.objects.create(
            name='allow', body=json.dumps(USER_CLAUSES)
        )

        self.user = UserFactory.create()
        setattr(self.request, 'user', self.user)

    def test_get_with_user(self):
        assign_user_policies(self.user, self.policy)
        response = self.view(self.request).render()
        content = response.content.decode('utf-8')

        self.u1.org_names = 'A, B'
        self.u2.org_names = 'B'
        self.u3.org_names = '&mdash;'
        self.user.org_names = '&mdash;'

        users = [self.u1, self.u2, self.u3, self.user]

        expected = render_to_string(
            'organization/user_list.html',
            {'object_list': users,
             'user': self.request.user},
            request=self.request)

        assert response.status_code == 200
        assert expected == content

    def test_get_with_unauthorized_user(self):
        response = self.view(self.request)
        assert response.status_code == 302

    def test_get_with_unauthenticated_user(self):
        setattr(self.request, 'user', AnonymousUser())
        response = self.view(self.request)
        assert response.status_code == 302
        assert '/account/login/' in response['location']


class UserActivationTest(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        setattr(self.request, 'method', 'POST')

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.policy = Policy.objects.create(
            name='allow', body=json.dumps(USER_CLAUSES)
        )
        self.users = UserFactory.create_from_kwargs([
            {'is_active': True},
            {'is_active': True},
            {'is_active': False}
        ])
        self.user = UserFactory.create(is_active=True)
        setattr(self.request, 'user', self.user)
        self.users.append(self.user)

    def _post(self, user_index_or_dummy, before, set, after,
              status=None, user_redirect=False, login_redirect=False,
              fail_message=False, raises_404=False):
        view = default.UserActivation.as_view(new_state=set)
        username = user_index_or_dummy
        mod_user = None
        if not isinstance(user_index_or_dummy, str):
            mod_user = self.users[user_index_or_dummy]
            username = mod_user.username
            assert mod_user.is_active is before
        if raises_404:
            with pytest.raises(Http404):
                response = view(self.request, user=username)
        else:
            response = view(self.request, user=username)
            if status is not None:
                assert response.status_code == status
            if user_redirect:
                assert '/users/' in response['location']
            if login_redirect:
                assert '/account/login/' in response['location']
            if fail_message:
                assert ("You don't have permission to update user details" in
                        [str(m) for m in get_messages(self.request)])
            if not isinstance(user_index_or_dummy, str):
                mod_user.refresh_from_db()
                assert mod_user.is_active is after

    def test_activate_valid(self):
        self.user.assign_policies(self.policy)
        self._post(2, False, True, True, status=302, user_redirect=True)
        self._post(0, True, True, True, status=302, user_redirect=True)

    def test_deactivate_valid(self):
        self.user.assign_policies(self.policy)
        self._post(1, True, False, False, status=302, user_redirect=True)
        self._post(2, False, False, False, status=302, user_redirect=True)

    def test_activate_nonexistent_user(self):
        self.user.assign_policies(self.policy)
        self._post('baduser', False, True, True, raises_404=True)

    def test_deactivate_nonexistent_user(self):
        self.user.assign_policies(self.policy)
        self._post('baduser', True, False, False, raises_404=True)

    def test_activate_unauthorized(self):
        self._post(2, False, True, False, status=302, fail_message=True)
        self._post(0, True, True, True, status=302, fail_message=True)

    def test_deactivate_unauthorized(self):
        self._post(1, True, False, True, status=302, fail_message=True)
        self._post(2, False, False, False, status=302, fail_message=True)

    def test_activate_unauthenticated(self):
        setattr(self.request, 'user', AnonymousUser())
        self._post(2, False, True, False, status=302, login_redirect=True)
        self._post(0, True, True, True, status=302, login_redirect=True)

    def test_deactivate_unauthenticated(self):
        setattr(self.request, 'user', AnonymousUser())
        self._post(1, True, False, True, status=302, login_redirect=True)
        self._post(2, False, False, False, status=302, login_redirect=True)
