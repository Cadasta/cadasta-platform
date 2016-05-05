from base import FunctionalTest
from pages.Registration import RegistrationPage
from pages.Login import LoginPage
from pages.Dashboard import DashboardPage


class RegistrationTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        self.test_data = {
            'users': [{
                'username': 'default1',
                'password': 'password1',
            }]
        }
        self.load_test_data(self.test_data)

    def test_register_user(self):
        """An unregistered user can register with valid user details."""

        page = RegistrationPage(self)
        page.go_to()
        fields = page.get_fields()

        # Try to submit an empty form and check for validation errors.
        page.try_submit(err=['username', 'email', 'password1', 'password2'])

        # Fill in required fields one by one, try to submit and check
        # for errors.
        fields = page.get_fields()
        fields['username'].send_keys('user3')
        page.try_submit(err=['email', 'password1', 'password2'],
                        ok=['username'])
        fields = page.get_fields()
        fields['email'].send_keys('user3@example.net')
        page.try_submit(err=['password1', 'password2'],
                        ok=['username', 'email'])
        fields = page.get_fields()
        fields['password1'].send_keys('very_secret')
        page.try_submit(err=['password1', 'password2'],
                        ok=['username', 'email'])
        fields = page.get_fields()
        fields['password2'].send_keys('not_very_secret')
        page.try_submit(err=['password1'],
                        ok=['username', 'email', 'password2'])

        # Fill in extra fields, fill in final required form and submit
        fields = page.get_fields()
        fields['full_name'].send_keys('User Three')
        fields['password1'].clear()
        fields['password1'].send_keys('very_secret')
        fields['password2'].clear()
        fields['password2'].send_keys('very_secret')
        self.click_through(fields['register'], self.BY_ALERT)
        self.assert_has_message('alert', "signed in")

        dashboard_page = DashboardPage(self)
        assert dashboard_page.is_on_page()
        dashboard_page.get_dashboard_map()

        self.logout()

        # Log in as new user
        sign_in = LoginPage(self).setup('user3', 'very_secret')
        self.click_through(sign_in, self.BY_ALERT)

        assert dashboard_page.is_on_page()
        dashboard_page.get_dashboard_map()

    def test_register_duplicate_user(self):
        """Check that user cannot register with an existing username."""

        page = RegistrationPage(self)
        page.go_to()
        fields = page.get_fields()

        fields['username'].send_keys(self.test_data['users'][0]['username'])
        fields['email'].send_keys('b@lah.net')
        fields['password1'].send_keys('password123')
        fields['password2'].send_keys('password123')
        fields['full_name'].send_keys('Jane Doe')
        page.try_submit(err=['username'],
                        ok=['email', 'password1', 'password2',
                            'full_name'])
        assert page.is_on_page()
