from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.messages.storage.fallback import FallbackStorage

from accounts.tests.factories import UserFactory
from ..views.default import AccountProfile
from ..forms import ProfileForm


class ProfileTest(TestCase):
    def setUp(self):
        self.view = AccountProfile.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        # Mock up messages middleware.
        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_get_profile(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)

        response = self.view(self.request).render()
        content = response.content.decode('utf-8')

        form = ProfileForm(instance=user)
        context = RequestContext(self.request)
        context['form'] = form

        expected = render_to_string('accounts/profile.html', context)

        assert response.status_code == 200
        assert content == expected

    def test_update_profile(self):
        user = UserFactory.create(username='John')
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {
            'username': 'John',
            'email': user.email,
            'first_name': 'John',
            'last_name': 'Lennon',
        })

        self.view(self.request)

        user.refresh_from_db()
        assert user.first_name == 'John'
        assert user.last_name == 'Lennon'

    def test_get_profile_when_no_user_is_signed_in(self):
        response = self.view(self.request)
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_update_profile_when_no_user_is_signed_in(self):
        setattr(self.request, 'method', 'POST')

        response = self.view(self.request)
        assert response.status_code == 302
        assert '/account/login/' in response['location']
