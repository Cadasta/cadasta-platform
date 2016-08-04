import json
import pytest

from django.test import TestCase
from django.http import Http404

from tutelary.models import Policy, assign_user_policies
from skivvy import ViewTestCase
from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory
from ..views.default import UserList, UserActivation
from .factories import clause


def assign_policies(user):
    USER_CLAUSES = {
        'clause': [
            clause('allow', ['user.list']),
            clause('allow', ['user.update'], ['user/*'])
        ]
    }
    policy = Policy.objects.create(name='allow', body=json.dumps(USER_CLAUSES))
    assign_user_policies(user, policy)


class UserListTest(ViewTestCase, UserTestCase, TestCase):
    view_class = UserList
    template = 'organization/user_list.html'

    def setup_models(self):
        self.u1 = UserFactory.create()
        self.u2 = UserFactory.create()
        self.u3 = UserFactory.create()
        self.org1 = OrganizationFactory.create(name='A', add_users=[self.u1])
        self.org2 = OrganizationFactory.create(
            name='B', add_users=[self.u1, self.u2]
        )
        self.user = UserFactory.create()

    def setup_template_context(self):
        self.u1.org_names = 'A, B'
        self.u2.org_names = 'B'
        self.u3.org_names = '&mdash;'
        self.user.org_names = '&mdash;'

        users = sorted([self.u1, self.u2, self.u3, self.user],
                       key=lambda u: u.username)
        return {'object_list': users,
                'user': self.user,
                'is_superuser': False}

    def test_get_with_user(self):
        assign_policies(self.user)
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 302

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location


class UserActivationTest(ViewTestCase, UserTestCase, TestCase):
    view_class = UserActivation

    def setup_models(self):
        self.user = UserFactory.create(is_active=True)

    def test_activate_valid(self):
        assign_policies(self.user)
        user = UserFactory.create(is_active=False)
        response = self.request(method='POST',
                                user=self.user,
                                url_kwargs={'user': user.username},
                                view_kwargs={'new_state': True})
        user.refresh_from_db()
        assert response.status_code == 302
        assert '/users/' in response.location
        assert user.is_active is True

    def test_deactivate_valid(self):
        assign_policies(self.user)
        user = UserFactory.create(is_active=True)
        response = self.request(method='POST',
                                user=self.user,
                                url_kwargs={'user': user.username},
                                view_kwargs={'new_state': False})
        user.refresh_from_db()
        assert response.status_code == 302
        assert '/users/' in response.location
        assert user.is_active is False

    def test_activate_nonexistent_user(self):
        assign_policies(self.user)
        with pytest.raises(Http404):
            self.request(method='POST',
                         user=self.user,
                         url_kwargs={'user': 'baduser'},
                         view_kwargs={'new_state': True})

    def test_deactivate_nonexistent_user(self):
        assign_policies(self.user)
        with pytest.raises(Http404):
            self.request(method='POST',
                         user=self.user,
                         url_kwargs={'user': 'baduser'},
                         view_kwargs={'new_state': False})

    def test_activate_unauthorized(self):
        user = UserFactory.create(is_active=False)
        response = self.request(method='POST',
                                user=self.user,
                                url_kwargs={'user': user.username},
                                view_kwargs={'new_state': True})
        user.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to update user details" in
                response.messages)
        assert user.is_active is False

    def test_deactivate_unauthorized(self):
        user = UserFactory.create(is_active=True)
        response = self.request(method='POST',
                                user=self.user,
                                url_kwargs={'user': user.username},
                                view_kwargs={'new_state': False})
        user.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to update user details" in
                response.messages)
        assert user.is_active is True

    def test_activate_unauthenticated(self):
        user = UserFactory.create(is_active=False)
        response = self.request(method='POST',
                                url_kwargs={'user': user.username},
                                view_kwargs={'new_state': True})
        user.refresh_from_db()
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert user.is_active is False

    def test_deactivate_unauthenticated(self):
        user = UserFactory.create(is_active=True)
        response = self.request(method='POST',
                                url_kwargs={'user': user.username},
                                view_kwargs={'new_state': False})
        user.refresh_from_db()
        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert user.is_active is True
