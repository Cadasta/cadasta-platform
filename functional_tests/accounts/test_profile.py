from base import FunctionalTest
from pages.Profile import ProfilePage
from pages.Login import LoginPage


class ProfileTest(FunctionalTest):
    def setUp(self):
        super().setUp()
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

        new_first_name = 'Kenny'
        new_last_name = 'Everett'

        fields['first_name'].clear()
        fields['first_name'].send_keys(new_first_name)
        fields['last_name'].clear()
        fields['last_name'].send_keys(new_last_name)
        page.submit_form()
        page.assert_profile_is_updated()

        self.logout()

        LoginPage(self).login(
            self.test_data['users'][0]['username'],
            self.test_data['users'][0]['password'],
        )

        page.go_to()
        fields = page.get_fields()
        assert fields['first_name'].get_attribute('value') == new_first_name
        assert fields['last_name'].get_attribute('value') == new_last_name
