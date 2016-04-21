from datetime import datetime, timezone
from base import FunctionalTest
from pages.Users import UsersPage
from pages.Login import LoginPage
from accounts.models import User
from accounts.tests.factories import UserFactory
from core.tests.factories import PolicyFactory, RoleFactory
from selenium.webdriver.common.by import By
from tutelary.models import Policy


class ActivationTest(FunctionalTest):

    def setUp(self):
        super().setUp()

        users = {}
        users['defaulta'] = UserFactory.create(
            username='defaulta',
            password='password1',
            is_active=False,
        )
        users['defaultb'] = UserFactory.create(
            username='defaultb',
            password='password1',
            is_active=True,
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
        # Default policy is installed automatically when first user is
        # created.
        pols['default'] = Policy.objects.get(name='default')
        pols['superuser'] = PolicyFactory.create(
            name='superuser', file='superuser.json'
        )

        roles = {}
        roles['superuser'] = RoleFactory.create(
            name='superuser',
            policies=[pols['default'], pols['superuser']],
        )

        users['superuser'].assign_policies(roles['superuser'])

    def check_inactive_login(self, username, password):
        """Check that inactive user cannot log in."""

        login_page = LoginPage(self).setup(username, password)
        self.click_through(login_page, (By.TAG_NAME, 'h1'))
        self.browser.find_element_by_xpath(
            "//h1[text()='Account Inactive' and not(*[2])]"
        )

    def access_direct_activate_urls(self):
        """Access the (de)activate URLs directly (GET method)."""

        # Note: Selenium cannot provide access to HTTP response codes
        # so we can't check that the server returns an HTTP error

        for user in User.objects.all():
            self.browser.get("{}/users/{}/activate/".format(
                self.live_server_url,
                user.username
            ))
            self.browser.get("{}/users/{}/deactivate/".format(
                self.live_server_url,
                user.username
            ))

    def check_user_status(self, statuses):
        """Check that the named users have the specified state
        by looking at the state of the activate/deactivate button
        on the users management page."""

        LoginPage(self).login('superuser', 'password2')
        UsersPage(self).go_to()

        tableBody = self.browser.find_element_by_xpath(
            "//table[@id='DataTables_Table_0']/tbody"
        )

        for username in iter(statuses.keys()):
            is_active = statuses[username]
            tableBody.find_element_by_xpath(
                "tr[./td[1][text()='{}' and not(*[2])]]".format(username) +
                "/td[5][form[@action='/users/{}/{}/']]".format(
                    username,
                    'deactivate' if is_active else 'activate'
                )
            )

    def generic_test_direct_url_access(self, username='', password=''):
        """Accessing the (de)activate URLs directly should have no effect."""

        statuses = {}
        for user in User.objects.all():
            statuses[user.username] = user.is_active

        if username:
            LoginPage(self).login(username, password)
        self.access_direct_activate_urls()
        if username:
            self.browser.get(self.live_server_url)
            self.logout()
        self.check_user_status(statuses)

    def generic_test_de_activate_user(self, username, password, is_active):
        """(De)activating a user does make the user (in)active."""

        # Cache default state
        statuses = {}
        for user in User.objects.all():
            statuses[user.username] = user.is_active

        # Activate user
        LoginPage(self).login('superuser', 'password2')
        UsersPage(self).go_to()
        button = self.browser.find_element_by_xpath(
            "//tr[./td[1][text()='{}']]".format(username) +
            "/td[5]//form[@action='/users/{}/{}/']//button".format(
                username,
                'deactivate' if is_active else 'activate'
            )
        )
        self.click_through(
            button,
            (
                By.XPATH,
                "//tr[./td[1][text()='{}']]/td[5]".format(username) +
                "//form[@action='/users/{}/{}/']//button".format(
                    username,
                    'activate' if is_active else 'deactivate'
                )
            )
        )
        self.logout()

        # Check that activated user can now log in
        if not is_active:
            LoginPage(self).login(username, password)
            self.logout()

        # Check that deactivated user cannot log in
        if is_active:
            self.check_inactive_login(username, password)

        # Check that status of all users are OK
        statuses[username] = not is_active
        self.check_user_status(statuses)

    def test_inactive_user(self):
        self.check_inactive_login('defaulta', 'password1')

    def test_nonloggedin_user_direct_url_access(self):
        self.generic_test_direct_url_access()

    def test_nonsuperuser_direct_url_access(self):
        self.generic_test_direct_url_access('defaultb', 'password1')

    def test_superuser_direct_url_access(self):
        self.generic_test_direct_url_access('superuser', 'password2')

    def test_activate_user(self):
        self.generic_test_de_activate_user('defaulta', 'password1', False)

    def test_deactivate_user(self):
        self.generic_test_de_activate_user('defaultb', 'password1', True)
