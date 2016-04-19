from base import FunctionalTest
from pages.Users import UsersPage
from pages.Login import LoginPage
from pages.Dashboard import DashboardPage


class PageAccessTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        self.test_data = {
            'user1': {
                'username': 'default1',
                'password': 'password1',
            },
            'superuser': {
                'username': 'superuser',
                'password': 'password2',
                '_is_superuser': True,
            },
        }
        self.test_data['users'] = (
            self.test_data['user1'],
            self.test_data['superuser'],
        )
        self.load_test_data(self.test_data)

    def test_nonloggedin_user(self):
        """A non-logged-in user cannot access the users page,
        but will be directed to it once logged in as a superuser."""

        self.browser.get(UsersPage(self).url)
        assert LoginPage(self).is_on_page()
        assert self.get_url_query() == 'next=' + UsersPage.path

        LoginPage(self).login(
            self.test_data['superuser']['username'],
            self.test_data['superuser']['password'],
        )
        assert UsersPage(self).is_on_page()

    def test_nonsuperuser(self):
        """A logged-in non-superuser cannot access the users page."""

        LoginPage(self).login(
            self.test_data['user1']['username'],
            self.test_data['user1']['password'],
        )
        self.browser.get(UsersPage(self).url)
        self.assert_has_message('alert', "have permission")
        assert DashboardPage(self).is_on_page()

    def test_superuser(self):
        """A logged-in superuser can access the users page."""

        LoginPage(self).login(
            self.test_data['superuser']['username'],
            self.test_data['superuser']['password'],
        )
        UsersPage(self).go_to()
        assert UsersPage(self).is_on_page()
