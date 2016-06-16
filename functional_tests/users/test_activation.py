from base import FunctionalTest
from pages.Users import UsersPage
from pages.Login import LoginPage
from pages.AccountInactive import AccountInactivePage
from core.tests.factories import PolicyFactory


class ActivationTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        self.test_data = {
            'inactive_user': {
                'username': 'default1',
                'password': 'password1',
                'is_active': False,
            },
            'active_user': {
                'username': 'default2',
                'password': 'password2',
                'is_active': True,
            },
            'superuser': {
                'username': 'superuser',
                'password': 'password3',
                'is_active': True,
                '_is_superuser': True,
            },
        }
        self.test_data['users'] = (
            self.test_data['inactive_user'],
            self.test_data['active_user'],
            self.test_data['superuser'],
        )
        self.load_test_data(self.test_data)

    # ---------- TEST HELPER FUNCTIONS ----------

    def check_inactive_login(self, user_data):
        """Check that inactive user cannot log in."""

        LoginPage(self).login_inactive(
            user_data['username'],
            user_data['password'],
        )
        assert AccountInactivePage(self).is_on_page()

    def access_direct_activate_urls(self):
        """Access the (de)activate URLs directly (GET method)."""

        # Note: Selenium cannot provide access to HTTP response codes
        # so we can't check that the server returns an HTTP error

        users_page = UsersPage(self)
        for user_data in self.test_data['users']:
            users_page.go_to_activate_user_url(user_data['username'])
            users_page.go_to_deactivate_user_url(user_data['username'])

    def check_user_status(self, statuses):
        """Check that the named users have the specified state
        by looking at the state of the activate/deactivate button
        on the users management page."""

        LoginPage(self).login(
            self.test_data['superuser']['username'],
            self.test_data['superuser']['password'],
        )
        users_page = UsersPage(self)
        users_page.go_to()
        for username in iter(statuses.keys()):
            assert (
                users_page.is_user_active(username) ==
                bool(statuses[username])
            )

    # ---------- GENERIC TESTS ----------

    def generic_test_direct_url_access(self, user_data=None):
        """Accessing the (de)activate URLs directly should have no effect."""

        statuses = {}
        for user in self.test_data['users']:
            statuses[user['username']] = user['is_active']

        if user_data:
            LoginPage(self).login(
                user_data['username'],
                user_data['password'],
            )
        self.access_direct_activate_urls()
        self.browser.get(self.live_server_url)
        if user_data:
            self.logout()
        self.check_user_status(statuses)

    def generic_test_de_activate_user(self, user_data):
        """(De)activating a user does make the user (in)active."""

        # Cache default state
        statuses = {}
        for user in self.test_data['users']:
            statuses[user['username']] = user['is_active']

        # Activate/deactivate user using the superuser
        LoginPage(self).login(
            self.test_data['superuser']['username'],
            self.test_data['superuser']['password'],
        )
        users_page = UsersPage(self)
        users_page.go_to()
        users_page.click_de_activate_button(user_data['username'])
        self.logout()

        # Check that activated user can now log in
        if not user_data['is_active']:
            LoginPage(self).login(
                user_data['username'],
                user_data['password'],
            )
            self.logout()

        # Check that deactivated user cannot log in
        if user_data['is_active']:
            self.check_inactive_login(user_data)

        # Check that status of all users are OK
        statuses[user_data['username']] = not user_data['is_active']
        self.check_user_status(statuses)

    # ---------- ACTUAL SPECIFIC TESTS ----------

    def test_inactive_user(self):
        self.check_inactive_login(self.test_data['inactive_user'])

    def test_nonloggedin_user_direct_url_access(self):
        self.generic_test_direct_url_access()

    def test_nonsuperuser_direct_url_access(self):
        self.generic_test_direct_url_access(self.test_data['active_user'])

    def test_superuser_direct_url_access(self):
        self.generic_test_direct_url_access(self.test_data['superuser'])

    def test_activate_user(self):
        self.generic_test_de_activate_user(self.test_data['inactive_user'])

    def test_deactivate_user(self):
        self.generic_test_de_activate_user(self.test_data['active_user'])
