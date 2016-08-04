from django.test import TestCase
from skivvy import ViewTestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from ..views.default import AccountProfile
from ..forms import ProfileForm


class ProfileTest(ViewTestCase, UserTestCase, TestCase):
    view_class = AccountProfile
    template = 'accounts/profile.html'

    def setup_template_context(self):
        return {
            'form': ProfileForm(instance=self.user)
        }

    def test_get_profile(self):
        self.user = UserFactory.create()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_update_profile(self):
        user = UserFactory.create(username='John')
        post_data = {
            'username': 'John',
            'email': user.email,
            'full_name': 'John Lennon'
        }
        response = self.request(method='POST', post_data=post_data, user=user)
        response.status_code == 200

        user.refresh_from_db()
        assert user.full_name == 'John Lennon'

    def test_get_profile_when_no_user_is_signed_in(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_update_profile_when_no_user_is_signed_in(self):
        response = self.request(method='POST', post_data={})
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_update_profile_duplicate_email(self):
        user1 = UserFactory.create(username='John',
                                   full_name='John Lennon')
        user2 = UserFactory.create(username='Bill')
        post_data = {
            'username': 'Bill',
            'email': user1.email,
            'full_name': 'Bill Bloggs',
        }

        response = self.request(method='POST', user=user2, post_data=post_data)
        assert 'Failed to update profile information' in response.messages
