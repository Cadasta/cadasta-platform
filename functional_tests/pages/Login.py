from .base import Page


class LoginPage(Page):
    def __init__(self, test):
        super(LoginPage, self).__init__(test)
        self.url = self.test.ui_url + '/account/login/'

    def go_to(self):
        self.browser.get(self.url)
        self.test.wait_for(self.get_form)
        return self

    def get_form(self):
        return self.test.form('login-form')

    def get_form_field(self, xpath):
        return self.test.form_field('login-form', xpath)

    def get_username_input(self):
        return self.get_form_field("input[@name='username']")

    def get_password_input(self):
        return self.get_form_field("input[@name='password']")

    def get_sign_in_button(self):
        return self.get_form_field("button[@name='sign-in']")

    def setup(self, username, password):
        """Go to login page and set up user and password fields."""
        self.go_to()
        self.get_username_input().send_keys(username)
        self.get_password_input().send_keys(password)
        return self.get_sign_in_button()

    def login(self, username, password):
        self.test.click_through(self.setup(username, password),
                                self.test.BY_ALERT)
