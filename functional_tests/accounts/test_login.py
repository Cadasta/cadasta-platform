from base import FunctionalTest
from pages.Login import LoginPage
from pages.Dashboard import DashboardPage

from core.tests.factories import PolicyFactory


class LoginTest(FunctionalTest):
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

    def test_unregistered_user(self):
        """An unregistered user cannot log in."""

        login_page = LoginPage(self)
        sign_in_button = login_page.setup('baduser', 'password')
        self.click_through(sign_in_button, self.BY_ALERT)
        login_page.assert_login_is_incorrect()

    def test_wrong_password(self):
        """An user cannot log in with an invalid password."""

        login_page = LoginPage(self)
        sign_in_button = login_page.setup(
            self.test_data['users'][0]['username'],
            self.test_data['users'][0]['password'] + 'wrong',
        )
        self.click_through(sign_in_button, self.BY_ALERT)
        login_page.assert_login_is_incorrect()

    def test_valid_login(self):
        """A registered user can log in with their username and password
        and log out again. The logged in and logged out states
        are persistent across page refreshes."""

        sign_in_button = LoginPage(self).setup(
            self.test_data['users'][0]['username'],
            self.test_data['users'][0]['password'],
        )
        self.click_through(sign_in_button, self.BY_ALERT)

        dashboard_page = DashboardPage(self)
        assert dashboard_page.is_on_page()
        dashboard_page.get_dashboard_map()

        self.browser.refresh()
        self.wait_for_no_alerts()
        dashboard_page.get_dashboard_map()

        self.logout()

        self.browser.refresh()
        self.wait_for_no_alerts()
        assert LoginPage(self).is_on_page()
