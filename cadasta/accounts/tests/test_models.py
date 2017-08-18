from datetime import datetime
from django.conf import settings
from django.test import TestCase

from .factories import UserFactory


class UserTest(TestCase):
    def test_repr(self):
        date = datetime.now()
        user = UserFactory.build(username='John',
                                 full_name='John Lennon',
                                 email='john@beatles.uk',
                                 email_verified=True,
                                 verify_email_by=date)
        assert repr(user) == ('<User username=John'
                              ' full_name=John Lennon'
                              ' email=john@beatles.uk'
                              ' email_verified=True'
                              ' verify_email_by={}>').format(date)

    def test_avatar_url_property_with_avatar_field_empty(self):
        user = UserFactory.build(username='John',
                                 full_name='John Lennon',
                                 email='john@beatles.uk',
                                 )
        assert user.avatar_url == settings.DEFAULT_AVATAR

    def test_avatar_url_property_with_avatar_field_set(self):
        test_avatar_path = '/accounts/tests/files/avatar.png'
        user = UserFactory.build(username='John',
                                 full_name='John Lennon',
                                 email='john@beatles.uk',
                                 avatar=test_avatar_path,
                                 )
        assert user.avatar_url == user.avatar.url
