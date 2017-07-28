from core.roles import PublicUserRole, AnonymousUserRole, UserRole
from django.test import TestCase
from core.tests.utils.cases import UserTestCase


class TestRoles(UserTestCase, TestCase):
    def test_anonymous_user_role(self):
        role = AnonymousUserRole()
        assert len(role.permissions) == 4

    def test_public_user_role(self):
        role = PublicUserRole()
        assert len(role.permissions) == 5

    def test_user_role(self):
        role = UserRole()
        assert role.permissions == []
