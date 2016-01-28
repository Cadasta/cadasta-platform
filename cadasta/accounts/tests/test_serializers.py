import pytest
from datetime import datetime
from django.test import TestCase

from ..serializers import RegistrationSerializer, AccountLoginSerializer
from ..models import User
from ..exceptions import EmailNotVerifiedError

from .factories import UserFactory


class RegistrationSerializerTest(TestCase):
    def test_field_serialization(self):
        user = UserFactory.build()
        serializer = RegistrationSerializer(user)
        self.assertIn('email_verified', serializer.data)
        self.assertNotIn('password', serializer.data)

    def test_create_with_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'first_name': 'John',
            'last_name': 'Lennon',
        }

        serializer = RegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        serializer.save()
        self.assertEqual(User.objects.count(), 1)

        user_obj = User.objects.first()
        self.assertTrue(user_obj.check_password(data['password']))
        self.assertTrue(user_obj.is_active)
        self.assertFalse(user_obj.email_verified)

    def test_create_without_email(self):
        """Serialiser should be invalid when no email address is provided."""

        data = {
            'username': 'imagine71',
            'password': 'iloveyoko79',
            'password_repeat': 'iloveyoko79',
            'first_name': 'John',
            'last_name': 'Lennon',
        }

        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_create_with_existing_email(self):
        """Serialiser should be invalid when another user with the same email
           address is already registered."""

        UserFactory.create(**{
            'email': 'john@beatles.uk',
        })

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'password_repeat': 'iloveyoko79',
            'first_name': 'John',
            'last_name': 'Lennon',
        }

        serializer = RegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Another user is already registered with this email address",
            serializer._errors['email'],
        )


class AccountLoginSerializerTest(TestCase):
    def test_unverified_account(self):
        """Serializer should raise EmailNotVerifiedError exeception when the
           user has not verified their email address within 48 hours"""

        user = UserFactory.create(**{
          'username': 'sgt_pepper',
          'password': 'iloveyoko79',
          'verify_email_by': datetime.now()
        })

        with pytest.raises(EmailNotVerifiedError):
            AccountLoginSerializer().validate(attrs={
                'username': 'sgt_pepper',
                'password': 'iloveyoko79'
            })
