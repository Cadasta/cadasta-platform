import random
import pytest
from datetime import datetime
from django.utils.translation import gettext as _
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request

from core.tests.utils.cases import UserTestCase
from ..serializers import (
    RegistrationSerializer, UserSerializer, AccountLoginSerializer
)
from ..models import User
from ..exceptions import EmailNotVerifiedError

from .factories import UserFactory


BASIC_TEST_DATA = {
    'username': 'imagine71',
    'email': 'john@beatles.uk',
    'password': 'iloveyoko79',
    'full_name': 'John Lennon',
}


class RegistrationSerializerTest(UserTestCase, TestCase):
    def test_field_serialization(self):
        user = UserFactory.build()
        serializer = RegistrationSerializer(user)
        assert 'email_verified' in serializer.data
        assert 'password' not in serializer.data

    def test_create_with_valid_data(self):
        serializer = RegistrationSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid()

        serializer.save()
        assert User.objects.count() == 1

        user_obj = User.objects.first()
        assert user_obj.check_password(BASIC_TEST_DATA['password'])
        assert user_obj.is_active
        assert not user_obj.email_verified

    def test_create_without_email(self):
        """Serialiser should be invalid when no email address is provided."""

        data = {
            'username': 'imagine71',
            'password': 'iloveyoko79',
            'password_repeat': 'iloveyoko79',
            'full_name': 'John Lennon',
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()

    def test_create_with_existing_email(self):
        """Serialiser should be invalid when another user with the same email
           address is already registered."""

        UserFactory.create(email='john@beatles.uk')

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'password_repeat': 'iloveyoko79',
            'full_name': 'John Lennon',
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert (_("Another user is already registered with this email address")
                in serializer._errors['email'])

    def test_create_with_restricted_username(self):
        invalid_usernames = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'username': random.choice(invalid_usernames),
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'password_repeat': 'iloveyoko79',
            'full_name': 'John Lennon',
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert (_("Username cannot be “add” or “new”.")
                in serializer._errors['username'])


class UserSerializerTest(UserTestCase, TestCase):
    def test_field_serialization(self):
        user = UserFactory.build()
        serializer = UserSerializer(user)
        assert 'email_verified' in serializer.data
        assert 'password' not in serializer.data

    def test_create_with_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon',
            'last_login': '2016-01-01 23:00:00'
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()

        serializer.save()
        assert User.objects.count() == 1

        user_obj = User.objects.first()
        assert user_obj.is_active
        assert not user_obj.email_verified

    def test_update_username_fails(self):
        serializer = UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid()
        user = serializer.save()
        other_user = UserFactory.create()
        update_data = {'username': 'bad-update'}
        request = APIRequestFactory().patch('/user/imagine71', update_data)
        force_authenticate(request, user=other_user)
        serializer2 = UserSerializer(
            user, update_data, context={'request': Request(request)}
        )
        assert not serializer2.is_valid()
        assert serializer2.errors['username'] == ['Cannot update username']

    def test_update_last_login_fails(self):
        serializer = UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid()
        user = serializer.save()
        update_data1 = {'username': 'imagine71',
                        'email': 'john@beatles.uk',
                        'last_login': '2016-01-01 23:00:00'}
        serializer2 = UserSerializer(user, data=update_data1)
        assert not serializer2.is_valid()
        assert serializer2.errors['last_login'] == ['Cannot update last_login']

    def test_update_with_restricted_username(self):
        serializer = UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid()
        user = serializer.save()
        invalid_usernames = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'username': random.choice(invalid_usernames),
            'email': 'john@beatles.uk',
            'full_name': 'John Lennon',
        }
        request = APIRequestFactory().patch('/user/imagine71', data)
        force_authenticate(request, user=user)
        serializer2 = UserSerializer(
            user, data=data, context={'request': Request(request)}
        )
        assert not serializer2.is_valid()
        assert serializer2.errors['username'] == [
            _("Username cannot be “add” or “new”.")]


class AccountLoginSerializerTest(UserTestCase, TestCase):
    def test_unverified_account(self):
        """Serializer should raise EmailNotVerifiedError exeception when the
           user has not verified their email address within 48 hours"""

        UserFactory.create(username='sgt_pepper',
                           password='iloveyoko79',
                           verify_email_by=datetime.now())

        with pytest.raises(EmailNotVerifiedError):
            AccountLoginSerializer().validate(attrs={
                'username': 'sgt_pepper',
                'password': 'iloveyoko79'
            })
