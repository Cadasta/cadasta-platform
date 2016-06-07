from base import FunctionalTest
from pages.Profile import ProfilePage
from pages.Login import LoginPage
from core.tests.factories import PolicyFactory


class ProfileTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        self.test_data = {
            'users': [{
                'username': 'default1',
                'password': 'password1',
            }]
        }
        self.load_test_data(self.test_data)

    def test_profile_view_and_edit(self):
        """A registered user can view and edit their profile."""

        LoginPage(self).login(
            self.test_data['users'][0]['username'],
            self.test_data['users'][0]['password'],
        )

        page = ProfilePage(self)
        page.go_to()
        fields = page.get_fields()

        new_full_name = 'Kenny Everett'

        fields['full_name'].clear()
        fields['full_name'].send_keys(new_full_name)
        page.submit_form()
        page.assert_profile_is_updated()

        self.logout()

        LoginPage(self).login(
            self.test_data['users'][0]['username'],
            self.test_data['users'][0]['password'],
        )

        page.go_to()
        fields = page.get_fields()
        assert fields['full_name'].get_attribute('value') == new_full_name
