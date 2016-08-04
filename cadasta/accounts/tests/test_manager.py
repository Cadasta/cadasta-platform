from pytest import raises

from django.test import TestCase

from ..models import User
from .factories import UserFactory
from core.tests.utils.cases import UserTestCase


class UserManagerTest(UserTestCase, TestCase):
    def test_get_from_usernamel(self):
        user = UserFactory.create()
        found = User.objects.get_from_username_or_email(
            identifier=user.username
        )

        assert found == user

    def test_get_from_email(self):
        user = UserFactory.create()
        found = User.objects.get_from_username_or_email(identifier=user.email)

        assert found == user

    def test_user_not_found(self):
        with raises(User.DoesNotExist):
            User.objects.get_from_username_or_email(identifier='username')

    def test_mulitple_users_found(self):
        UserFactory.create(username='user@example.com')
        UserFactory.create(email='user@example.com')

        with raises(User.MultipleObjectsReturned):
            User.objects.get_from_username_or_email(
                identifier='user@example.com'
            )
