from base import FunctionalTest
from fixtures import load_test_data
from pages.Registration import RegistrationPage
from pages.Login import LoginPage
from pages.Dashboard import DashboardPage
from core.tests.factories import PolicyFactory


class RegistrationTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        self.test_data = {
            'users': [{
                'username': 'default1',
                'password': 'password1',
            }]
        }
        load_test_data(self.test_data)

    def test_register_user(self):
        """An unregistered user can register with valid user details."""

        page = RegistrationPage(self)
        page.go_to()
        fields = page.get_fields()

        # Try to submit an empty form and check for validation errors.
        page.try_submit(err=['username', 'email', 'password'])

        # Fill in required fields one by one, try to submit and check
        # for errors.
        fields = page.get_fields()
        fields['username'].send_keys('user3')
        page.try_submit(err=['email', 'password'],
                        ok=['username'],)
        fields = page.get_fields()
        fields['email'].send_keys('user3@example.net')
        page.try_submit(err=['password'],
                        ok=['username', 'email'],)

        # Fill in extra fields, fill in final required form and submit
        fields = page.get_fields()
        fields['full_name'].send_keys('User Three')
        fields['password'].clear()
        fields['password'].send_keys('very_secret')
        self.click_through(fields['register'], self.BY_DASHBOARD)
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
        fields['password'].send_keys('password123')
        fields['full_name'].send_keys('Jane Doe')
        page.try_submit(err=['username'],
                        ok=['email', 'password',
                            'full_name'],
                        message='A user with that username already exists.')
        assert page.is_on_page()
