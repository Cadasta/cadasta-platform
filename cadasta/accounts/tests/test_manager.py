from pytest import raises

from django.test import TestCase

from ..models import User
from .factories import UserFactory
from core.tests.utils.cases import UserTestCase


class UserManagerTest(UserTestCase, TestCase):
    def test_get_from_username(self):
        user = UserFactory.create()
        found = User.objects.get_from_username_or_email_or_phone(
            identifier=user.username
        )

        assert found == user

    def test_get_from_username_non_case_sensitive(self):
        user = UserFactory.create(username='TestUser')
        found = User.objects.get_from_username_or_email_or_phone(
            identifier='testuser'
        )

        assert found == user

    def test_get_from_email(self):
        user = UserFactory.create()
        found = User.objects.get_from_username_or_email_or_phone(
            identifier=user.email)

        assert found == user

    def test_get_from_email_non_case_sensitive(self):
        user = UserFactory.create(email='TestUser@example.com')
        found = User.objects.get_from_username_or_email_or_phone(
            identifier='testuser@example.com')

        assert found == user

    def test_get_from_phone(self):
        user = UserFactory.create()
        found = User.objects.get_from_username_or_email_or_phone(
            identifier=user.phone
        )
        assert found == user

    def test_user_not_found(self):
        with raises(User.DoesNotExist):
            User.objects.get_from_username_or_email_or_phone(
                identifier='username')

    def test_mulitple_users_found(self):
        UserFactory.create(username='user@example.com')
        UserFactory.create(email='user@example.com')

        with raises(User.MultipleObjectsReturned):
            User.objects.get_from_username_or_email_or_phone(
                identifier='user@example.com'
            )
