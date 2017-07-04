import random
import pytest

from datetime import datetime
from django.utils.translation import gettext as _
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.request import Request

from core.messages import SANITIZE_ERROR
from core.tests.utils.cases import UserTestCase
from .. import serializers
from ..models import User
from ..exceptions import EmailNotVerifiedError

from .factories import UserFactory


BASIC_TEST_DATA = {
    'username': 'imagine71',
    'email': 'john@beatles.uk',
    'password': 'iloveyoko79!',
    'full_name': 'John Lennon',
    'language': 'en',
    'measurement': 'metric',
}


class RegistrationSerializerTest(UserTestCase, TestCase):
    def test_field_serialization(self):
        user = UserFactory.build()
        serializer = serializers.RegistrationSerializer(user)
        assert 'email_verified' in serializer.data
        assert 'password' not in serializer.data

    def test_create_with_valid_data(self):
        serializer = serializers.RegistrationSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid() is True

        serializer.save()
        assert User.objects.count() == 1

        user_obj = User.objects.first()
        assert user_obj.check_password(BASIC_TEST_DATA['password'])
        assert user_obj.is_active
        assert not user_obj.email_verified

    def test_case_insensitive_username(self):
        usernames = ['UsErOne', 'useRtWo', 'uSERthReE']
        users = [
            UserFactory.create(username=username) for username in usernames]
        for user in users:
            TEST_DATA = BASIC_TEST_DATA.copy()
            TEST_DATA['username'] = user.username.lower()
            serializer = serializers.RegistrationSerializer(data=TEST_DATA)
            assert serializer.is_valid() is False
            assert (_("A user with that username already exists")
                    in serializer._errors['username'])
        TEST_DATA = BASIC_TEST_DATA.copy()
        TEST_DATA['username'] = 'userFour'
        serializer = serializers.RegistrationSerializer(data=TEST_DATA)
        assert serializer.is_valid() is True
        serializer.save()
        assert User.objects.count() == 4

    def test_create_without_email(self):
        """Serialiser should be invalid when no email address is provided."""

        data = {
            'username': 'imagine71',
            'password': 'iloveyoko79!',
            'password_repeat': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }

        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False

    def test_sanitize(self):
        """Serialiser should be invalid when no email address is provided."""

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'password_repeat': 'iloveyoko79!',
            'full_name': '😀😃😄😁😆😅',
        }

        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert SANITIZE_ERROR in serializer.errors['full_name']

    def test_create_with_existing_email(self):
        """Serialiser should be invalid when another user with the same email
           address is already registered."""

        UserFactory.create(email='john@beatles.uk')

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'password_repeat': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }

        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert (_("Another user is already registered with this email address")
                in serializer._errors['email'])

    def test_create_with_restricted_username(self):
        invalid_usernames = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'username': random.choice(invalid_usernames),
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'password_repeat': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }

        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert (_('Username cannot be “add” or “new”.')
                in serializer._errors['username'])

    def test_password_contains_username(self):
        data = {
            'username': 'yoko79',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'password_repeat': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }
        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert (_("The password is too similar to the username.") in
                serializer._errors['password'])

    def test_password_contains_username_case_insensitive(self):
        data = {
            'username': 'yoko79',
            'email': 'john@beatles.uk',
            'password': 'iloveYOKO79!',
            'password_repeat': 'iloveYOKO79!',
            'full_name': 'John Lennon',
        }
        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert (_("The password is too similar to the username.") in
                serializer._errors['password'])

    def test_password_contains_blank_username(self):
        data = {
            'username': '',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'password_repeat': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }
        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert ('password' not in serializer._errors)

    def test_password_contains_email(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'johnisjustheBest!!',
            'password_repeat': 'johnisjustheBest!!',
            'full_name': 'John Lennon',
        }
        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert (_("Passwords cannot contain your email.") in
                serializer._errors['password'])

    def test_password_contains_blank_email(self):
        data = {
            'username': 'imagine71',
            'email': '',
            'password': 'johnisjustheBest!!',
            'password_repeat': 'johnisjustheBest!!',
            'full_name': 'John Lennon',
        }
        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert ('password' not in serializer._errors)

    def test_password_contains_less_than_min_characters(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'yoko<3',
            'password_repeat': 'yoko<3',
            'full_name': 'John Lennon',
        }
        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.") in
                serializer._errors['password'])

    def test_password_does_not_meet_unique_character_requirements(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko',
            'password_repeat': 'iloveyoko',
            'full_name': 'John Lennon',
        }
        serializer = serializers.RegistrationSerializer(data=data)
        assert serializer.is_valid() is False
        assert (_("Passwords must contain at least 3"
                  " of the following 4 character types:\n"
                  "lowercase characters, uppercase characters,"
                  " special characters, and/or numerical character.\n"
                  ) in serializer._errors['password'])


class UserSerializerTest(UserTestCase, TestCase):
    def test_field_serialization(self):
        user = UserFactory.build()
        serializer = serializers.UserSerializer(user)
        assert 'email_verified' in serializer.data
        assert 'password' not in serializer.data

    def test_create_with_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon',
            'last_login': '2016-01-01 23:00:00',
            'language': 'en',
            'measurement': 'metric',
        }
        serializer = serializers.UserSerializer(data=data)
        assert serializer.is_valid() is True

        serializer.save()
        assert User.objects.count() == 1

        user_obj = User.objects.first()
        assert user_obj.is_active
        assert not user_obj.email_verified

    def test_update_username_fails(self):
        serializer = serializers.UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid() is True
        user = serializer.save()
        other_user = UserFactory.create()
        update_data = {'username': 'bad-update'}
        request = APIRequestFactory().patch('/user/imagine71', update_data)
        force_authenticate(request, user=other_user)
        serializer2 = serializers.UserSerializer(
            user, update_data, context={'request': Request(request)}
        )
        assert serializer2.is_valid() is False
        assert serializer2.errors['username'] == ['Cannot update username']

    def test_case_insensitive_username(self):
        data = {
            'username': 'USERtwO',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon'
        }
        usernames = ['UsErOne', 'useRtWo', 'uSERthReE']
        users = [
            UserFactory.create(username=username) for username in usernames]
        request = APIRequestFactory().patch(
            '/user/userone', data)
        force_authenticate(request, user=users[0])
        serializer = serializers.UserSerializer(
            users[0], data, context={'request': Request(request)})
        assert serializer.is_valid() is False
        assert serializer.errors['username'] == [
            _("A user with that username already exists")
        ]

    def test_update_last_login_fails(self):
        serializer = serializers.UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid() is True
        user = serializer.save()
        update_data1 = {'username': 'imagine71',
                        'email': 'john@beatles.uk',
                        'last_login': '2016-01-01 23:00:00'}
        serializer2 = serializers.UserSerializer(user, data=update_data1)
        assert serializer2.is_valid() is False
        assert serializer2.errors['last_login'] == ['Cannot update last_login']

    def test_update_with_restricted_username(self):
        serializer = serializers.UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid() is True
        user = serializer.save()
        invalid_usernames = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'username': random.choice(invalid_usernames),
            'email': 'john@beatles.uk',
            'full_name': 'John Lennon',
        }
        request = APIRequestFactory().patch('/user/imagine71', data)
        force_authenticate(request, user=user)
        serializer2 = serializers.UserSerializer(
            user, data=data, context={'request': Request(request)}
        )
        assert serializer2.is_valid() is False
        assert serializer2.errors['username'] == [
            _("Username cannot be “add” or “new”.")]

    def test_update_with_invalid_language(self):
        serializer = serializers.UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid() is True
        user = serializer.save()
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'language': 'invalid',
        }
        request = APIRequestFactory().patch('/user/imagine71', data)
        force_authenticate(request, user=user)
        serializer2 = serializers.UserSerializer(
            user, data=data, context={'request': Request(request)}
        )
        assert serializer2.is_valid() is False
        assert ('Language invalid or not available'
                in serializer2.errors['language'])

    def test_update_with_invalid_measurement_system(self):
        serializer = serializers.UserSerializer(data=BASIC_TEST_DATA)
        assert serializer.is_valid() is True
        user = serializer.save()
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'measurement': 'invalid',
        }
        request = APIRequestFactory().patch('/user/imagine71', data)
        force_authenticate(request, user=user)
        serializer2 = serializers.UserSerializer(
            user, data=data, context={'request': Request(request)}
        )
        assert serializer2.is_valid() is False
        assert ('Measurement system invalid or not available'
                in serializer2.errors['measurement'])

    def test_sanitize(self):
        user = UserFactory.create(username='imagine71')
        data = {
            'full_name': '😀😃😄😁😆😅',
        }
        request = APIRequestFactory().patch('/user/imagine71', data)
        force_authenticate(request, user=user)
        serializer = serializers.UserSerializer(
            user, data=data, context={'request': Request(request)},
            partial=True
        )
        assert serializer.is_valid() is False
        assert SANITIZE_ERROR in serializer.errors['full_name']


class AccountLoginSerializerTest(UserTestCase, TestCase):
    def test_unverified_account(self):
        """Serializer should raise EmailNotVerifiedError exeception when the
           user has not verified their email address within 48 hours"""

        UserFactory.create(username='sgt_pepper',
                           password='iloveyoko79',
                           verify_email_by=datetime.now())

        with pytest.raises(EmailNotVerifiedError):
            serializers.AccountLoginSerializer().validate(attrs={
                'username': 'sgt_pepper',
                'password': 'iloveyoko79'
            })


class ChangePasswordSerializerTest(UserTestCase, TestCase):
    def test_user_can_change_pw(self):
        user = UserFactory.create(password='beatles4Lyfe!', change_pw=True)
        request = APIRequestFactory().patch('/user/imagine71', {})
        force_authenticate(request, user=user)
        data = {
            'current_password': 'beatles4Lyfe!',
            'new_password': 'iloveyoko79!',
            're_new_password': 'iloveyoko79!'
        }

        serializer = serializers.ChangePasswordSerializer(
            user, data=data, context={'request': Request(request)}
        )
        assert serializer.is_valid() is True

    def test_user_can_not_change_pw(self):
        user = UserFactory.create(password='beatles4Lyfe!', change_pw=False)
        request = APIRequestFactory().patch('/user/imagine71', {})
        force_authenticate(request, user=user)
        data = {
            'current_password': 'beatles4Lyfe!',
            'new_password': 'iloveyoko79!',
            're_new_password': 'iloveyoko79!'
        }

        serializer = serializers.ChangePasswordSerializer(
            user, data=data, context={'request': Request(request)}
        )
        assert serializer.is_valid() is False
        assert ("The password for this user can not be changed."
                in serializer.errors['non_field_errors'])

    def test_password_contains_username(self):
        user = UserFactory.create(
            password=BASIC_TEST_DATA['password'],
            username='imagine71',
        )
        request = APIRequestFactory().patch('/user/imagine71', {})
        force_authenticate(request, user=user)
        data = {
            'username': 'imagine71',
            'current_password': BASIC_TEST_DATA['password'],
            'new_password': 'Letsimagine71!12345',
            're_new_password': 'Letsimagine71!12345',
        }
        serializer = serializers.ChangePasswordSerializer(
            user, data=data, context={'request': Request(request)})

        assert serializer.is_valid() is False
        assert (_("The password is too similar to the username.")
                in serializer._errors['new_password'])

    def test_password_contains_username_case_insensitive(self):
        user = UserFactory.create(
            password=BASIC_TEST_DATA['password'],
            username='imagine71',
        )
        request = APIRequestFactory().patch('/user/imagine71', {})
        force_authenticate(request, user=user)
        data = {
            'username': 'imagine71',
            'current_password': BASIC_TEST_DATA['password'],
            'new_password': 'LetsIMAGINE71!12345',
            're_new_password': 'LetsIMAGINE71!12345',
        }
        serializer = serializers.ChangePasswordSerializer(
            user, data=data, context={'request': Request(request)})

        assert serializer.is_valid() is False
        assert (_("The password is too similar to the username.")
                in serializer._errors['new_password'])

    def test_password_contains_email(self):
        user = UserFactory.create(
            password=BASIC_TEST_DATA['password'],
            email=BASIC_TEST_DATA['email'],
            username='imagine71!',
        )
        request = APIRequestFactory().patch('/user/imagine71', {})
        force_authenticate(request, user=user)
        data = {
            'current_password': BASIC_TEST_DATA['password'],
            'new_password': 'JOHNisjustheBest!!',
            're_new_password': 'JOHNisjustheBest!!',
        }

        serializer = serializers.ChangePasswordSerializer(
            user, data=data, context={'request': Request(request)})
        assert serializer.is_valid() is False
        assert (_("Passwords cannot contain your email.")
                in serializer._errors['new_password'])

    def test_password_contains_less_than_min_characters(self):
        user = UserFactory.create(
            username='imagine71',
            password=BASIC_TEST_DATA['password'],
        )
        request = APIRequestFactory().patch('/user/imagine71', {})
        force_authenticate(request, user=user)

        data = {
            'current_password': BASIC_TEST_DATA['password'],
            'new_password': 'yoko<3',
            're_new_password': 'yoko<3',
        }

        serializer = serializers.ChangePasswordSerializer(
            user, data=data, context={'request': Request(request)})

        assert serializer.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.")
                in serializer._errors['new_password'])

    def test_password_does_not_meet_unique_character_requirements(self):
        user = UserFactory.create(
            username='imagine71',
            password=BASIC_TEST_DATA['password'],
        )
        request = APIRequestFactory().patch('/user/imagine71', {})
        force_authenticate(request, user=user)

        data = {
            'current_password': BASIC_TEST_DATA['password'],
            'new_password': 'iloveyoko',
            're_new_password': 'iloveyoko',
        }

        serializer = serializers.ChangePasswordSerializer(
            user, data=data, context={'request': Request(request)})

        assert serializer.is_valid() is False
        assert (_("Passwords must contain at least 3"
                  " of the following 4 character types:\n"
                  "lowercase characters, uppercase characters,"
                  " special characters, and/or numerical character.\n"
                  ) in serializer._errors['new_password'])
