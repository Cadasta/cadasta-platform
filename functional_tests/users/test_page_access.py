from selenium.webdriver.common.by import By

from base import FunctionalTest
from fixtures import load_test_data
from pages.Users import UsersPage
from pages.Login import LoginPage
from pages.Dashboard import DashboardPage
from core.tests.factories import PolicyFactory


class PageAccessTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        self.test_data = {
            'users': [
                {
                    'username': 'default1',
                    'password': 'password1',
                },
                {
                    'username': 'superuser',
                    'password': 'password2',
                    '_is_superuser': True,
                }
            ]
        }
        (self.user1, self.superuser) = self.test_data['users']
        load_test_data(self.test_data)

    def test_nonloggedin_user(self):
        """A non-logged-in user cannot access the users page,
        but will be directed to it once logged in as a superuser."""

        self.browser.get(UsersPage(self).url)
        assert LoginPage(self).is_on_page()
        assert self.get_url_query() == 'next=' + UsersPage.path

        LoginPage(self).login(self.superuser['username'],
                              self.superuser['password'],
                              wait=(By.ID, 'users'))
        assert UsersPage(self).is_on_page()

    def test_nonsuperuser(self):
        """A logged-in non-superuser cannot access the users page."""

        LoginPage(self).login(self.user1['username'],
                              self.user1['password'])
        self.browser.get(UsersPage(self).url)
        self.assert_has_message('alert', "have permission")
        assert DashboardPage(self).is_on_page()

    def test_superuser(self):
        """A logged-in superuser can access the users page."""

        LoginPage(self).login(self.superuser['username'],
                              self.superuser['password'])
        UsersPage(self).go_to()
        assert UsersPage(self).is_on_page()

    def test_user_list_link_nonloggedin_user(self):
        """A non-logged-in superuser should NOT see the "Users" link in the
        navbar.

        """
        DashboardPage(self).go_to()
        self.get_screenshot('dash')
        ulink = DashboardPage(self).has_nav_link('Users')
        print(ulink)
        plink = DashboardPage(self).has_nav_link('Projects')
        print(plink)
        assert not DashboardPage(self).has_nav_link('Users')

    def test_user_list_link_nonsuperuser(self):
        """A logged-in non-superuser should NOT see the "Users" link in the
        navbar.

        """
        LoginPage(self).login(self.user1['username'], self.user1['password'])
        DashboardPage(self).go_to()
        assert not DashboardPage(self).has_nav_link('Users')

    def test_user_list_link_superuser(self):
        """A logged-in superuser should see the "Users" link in the navbar.

        """
        LoginPage(self).login(self.superuser['username'],
                              self.superuser['password'])
        DashboardPage(self).go_to()
        assert DashboardPage(self).has_nav_link('Users')
