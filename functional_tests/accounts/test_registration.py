from base import FunctionalTest
from pages.Registration import RegistrationPage
from pages.Login import LoginPage
from accounts.models import User


class RegistrationTest(FunctionalTest):
    def setUp(self):
        user1 = User(username='user1', email='user1@example.org',
                     first_name='User', last_name='One')
        user1.set_password('user1pwd')
        user1.save()

    def test_register_user(self):
        """An unregistered user can register with valid user details."""

        page = RegistrationPage(self)
        page.go_to()
        fields = page.get_fields()

        # Try to submit an empty form and check for validation errors.
        page.try_submit(err=['username', 'email',
                             'password', 'password_repeat'])

        # Fill in required fields one by one, try to submit and check
        # for errors.
        fields['username'].send_keys('user3')
        page.try_submit(err=['email', 'password', 'password_repeat'],
                        ok=['username'])
        fields['email'].send_keys('user3@example.net')
        page.try_submit(err=['password', 'password_repeat'],
                        ok=['username', 'email'])
        fields['password'].send_keys('very_secret')
        page.try_submit(err=['password_repeat'],
                        ok=['username', 'email', 'password'])
        fields['password_repeat'].send_keys('not_very_secret')
        page.try_submit(err=['password_repeat'],
                        ok=['username', 'email', 'password'])

        # Fill in extra fields, fill in final required form and
        # submit.
        fields['first_name'].send_keys('User')
        fields['last_name'].send_keys('Three')
        fields['password_repeat'].clear()
        fields['password_repeat'].send_keys('very_secret')
        self.click_through(fields['register'], self.BY_ALERT)
        self.assert_has_message('alert', "logged in")
        self.browser.find_element_by_xpath("//h1[.='Dashboard']")

        # Log out.
        self.click_through(
            self.browser.find_element_by_xpath("//a[.='Logout']"),
            self.BY_ALERT
        )
        self.assert_has_message('alert', "logged out")

        # Log in as new user.
        sign_in = LoginPage(self).setup('user3', 'very_secret')
        self.click_through(sign_in, self.BY_ALERT)
        self.browser.find_element_by_xpath("//h1[.='Dashboard']")

    def test_register_duplicate_user(self):
        page = RegistrationPage(self)
        page.go_to()
        fields = page.get_fields()

        fields['username'].send_keys('user1')
        fields['email'].send_keys('b@lah.net')
        fields['password'].send_keys('password123')
        fields['password_repeat'].send_keys('password123')
        fields['first_name'].send_keys('Jane')
        fields['last_name'].send_keys('Doe')
        self.click_through(fields['register'], self.BY_ALERT)
        self.assert_has_message('alert',
                                "Unable to register with provided credentials")
        self.browser.find_element_by_xpath(
            "//h1[.='Sign up for a free account']"
        )
