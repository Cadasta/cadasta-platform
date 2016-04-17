from datetime import datetime, timezone
from base import FunctionalTest
from pages.Users import UsersPage
from pages.Login import LoginPage
from accounts.tests.factories import UserFactory
from core.tests.factories import PolicyFactory, RoleFactory


class PageAccessTest(FunctionalTest):

    def setUp(self):
        super().setUp()

        users = {}
        users['default'] = UserFactory.create(
            username='default',
            password='password1',
        )
        users['superuser'] = UserFactory.create(
            username='superuser',
            password='password2',
            email_verified=True,
            last_login=datetime.now(tz=timezone.utc),
            is_active=True,
        )

        pols = {}
        PolicyFactory.set_directory('../cadasta/config/permissions')
        pols['default'] = PolicyFactory.create(
            name='default',   file='default.json'
        )
        pols['superuser'] = PolicyFactory.create(
            name='superuser', file='superuser.json'
        )

        roles = {}
        roles['superuser'] = RoleFactory.create(
            name='superuser',
            policies=[pols['default'], pols['superuser']],
        )

        users['superuser'].assign_policies(roles['superuser'])

    def test_nonloggedin_user(self):
        """A non-logged-in user cannot access the users page,
        but will be directed to it once logged in as a superuser."""

        # Access as non-logged-in user
        users_page = UsersPage(self)
        self.browser.get(users_page.url)
        assert self.get_url_path() == '/account/login/?next=/users/'

        # Log in as superuser
        LoginPage(self).get_username_input().send_keys('superuser')
        LoginPage(self).get_password_input().send_keys('password2')
        self.click_through(
            LoginPage(self).get_sign_in_button(),
            self.BY_ALERT
        )
        assert self.get_url_path() == '/users/'

    def test_nonsuperuser(self):
        """A logged-in non-superuser cannot access the users page."""

        LoginPage(self).login('default', 'password1')
        users_page = UsersPage(self)
        self.browser.get(users_page.url)
        self.wait_for_alert()
        self.assert_has_message('alert', "have permission")
        assert self.get_url_path() == '/dashboard/'

    def test_superuser(self):
        """A logged-in superuser can access the users page."""

        LoginPage(self).login('superuser', 'password2')
        UsersPage(self).go_to()
        self.browser.find_element_by_xpath(
            "//h1[text()='Users' and not(*[2])]"
        )
