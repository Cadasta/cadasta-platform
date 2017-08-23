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

    def test_avatar_has_changed_property(self):
        first_avatar_path = '/accounts/tests/files/avatar.png'
        second_avatar_path = '/resources/tests/files/image.jpg'
        user1 = UserFactory.build(username='John',
                                  full_name='John Lennon',
                                  email='john@beatles.uk',
                                  avatar=first_avatar_path,
                                  )
        assert user1._avatar_has_changed is False

        user2 = UserFactory.build(username='John',
                                  full_name='John Lennon',
                                  email='john@beatles.uk',
                                  avatar=first_avatar_path,
                                  )
        user2.avatar.url = second_avatar_path
        assert user2._avatar_has_changed is True

    def test_avatar_is_custom_property(self):
        test_avatar_path = '/accounts/tests/files/avatar.png'
        user1 = UserFactory.build(username='John',
                                  full_name='John Lennon',
                                  email='john@beatles.uk',
                                  avatar=test_avatar_path,
                                  )
        assert user1._avatar_is_custom is True

        user2 = UserFactory.build(username='John',
                                  full_name='John Lennon',
                                  email='john@beatles.uk',
                                  avatar=settings.DEFAULT_AVATAR,
                                  )
        assert user2._avatar_is_custom is False

    def test_avatar_thumbnail_without_thumbnail_attribute(self):
        test_avatar_path = '/accounts/tests/files/avatar.png'
        user = UserFactory.build(username='John',
                                 full_name='John Lennon',
                                 email='john@beatles.uk',
                                 avatar=test_avatar_path,
                                 )
        avatar_thumbnail_path = user.avatar_thumbnail
        assert user._thumbnail == avatar_thumbnail_path
