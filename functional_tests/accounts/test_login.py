from base import FunctionalTest
from pages.Login import LoginPage
from accounts.tests.factories import UserFactory


class LoginTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        UserFactory.create(username='user1', password='user1pwd')

    def test_unregistered_user(self):
        """An unregistered user cannot log in."""

        sign_in = LoginPage(self).setup('baduser', 'password')
        self.click_through(sign_in, self.BY_ALERT)

        self.assert_has_message('alert', "not correct")

    def test_wrong_password(self):
        """An user cannot log in with an invalid password."""
        sign_in = LoginPage(self).setup('user1', 'not_right')
        self.click_through(sign_in, self.BY_ALERT)

        self.assert_has_message('alert', "not correct")

    def test_valid_login(self):
        """A registered user can log in with their username and password and
        log out again.  The logged in and logged out states are
        persistent across page refreshes.

        """
        sign_in = LoginPage(self).setup('user1', 'user1pwd')
        self.click_through(sign_in, self.BY_ALERT)
        self.browser.find_element_by_xpath(self.xpath('h1', 'Dashboard'))

        self.browser.refresh()
        self.wait_for_no_alerts()
        self.browser.find_element_by_xpath(self.xpath('h1', 'Dashboard'))

        self.click_through(
            self.browser.find_element_by_xpath(self.xpath('a', 'Logout')),
            self.BY_ALERT
        )
        self.assert_has_message('alert', "signed out")

        self.browser.refresh()
        self.wait_for_no_alerts()
        self.browser.find_element_by_xpath(
            self.xpath('h1', 'Sign in to your account')
        )
