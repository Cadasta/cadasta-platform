from .base import Page
from selenium.webdriver.common.by import By


class LoginPage(Page):

    path = '/account/login/'

    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + self.path

    def is_on_page(self):
        """Returns True if user is on this page"""
        return self.test.get_url_path() == self.path

    def go_to(self):
        if not self.is_on_page():
            self.browser.get(self.url)
        self.test.wait_for(self.get_form)
        return self

    def get_form(self):
        return self.test.form('login-form')

    def get_form_field(self, xpath):
        return self.test.form_field('login-form', xpath)

    def get_username_input(self):
        return self.get_form_field("input[@name='login']")

    def get_password_input(self):
        return self.get_form_field("input[@name='password']")

    def get_sign_in_button(self):
        return self.get_form_field("button[@name='sign-in']")

    def setup(self, username, password):
        """Go to login page and set up user and password fields."""
        self.go_to()
        self.get_username_input().clear()
        self.get_username_input().send_keys(username)
        self.get_password_input().clear()
        self.get_password_input().send_keys(password)
        return self.get_sign_in_button()

    def login(self, username, password, wait=(By.CLASS_NAME, 'dashboard-map')):
        self.test.click_through(self.setup(username, password), wait)

    def login_inactive(self, username, password):
        self.test.click_through(self.setup(username, password),
                                (By.TAG_NAME, 'h1'))

    def assert_login_is_incorrect(self):
        self.test.assert_has_message('alert', "not correct")
