from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class UserUrlsTest(TestCase):
    def test_profile(self):
        assert reverse('account:profile') == '/account/profile/'

        resolved = resolve('/account/profile/')
        assert resolved.func.__name__ == default.AccountProfile.__name__
