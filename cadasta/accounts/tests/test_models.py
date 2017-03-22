from datetime import datetime
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
                              ' file='
                              ' email_verified=True'
                              ' verify_email_by={}>').format(date)
