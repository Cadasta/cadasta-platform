from .base import Page


class ProfilePage(Page):

    path = '/account/profile/'

    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + self.path

    def is_on_page(self):
        """Returns True if user is on this page"""
        return self.test.get_url_path() == self.path

    def go_to(self):
        self.browser.get(self.url)
        self.test.wait_for(self.get_form)
        return self

    def get_form(self):
        return self.test.form('profile-form')

    def get_form_field(self, xpath):
        return self.test.form_field('profile-form', xpath)

    def get_username_input(self):
        return self.get_form_field("input[@name='username']")

    def get_email_input(self):
        return self.get_form_field("input[@name='email']")

    def get_full_name_input(self):
        return self.get_form_field("input[@name='full_name']")

    def get_update_button(self):
        return self.get_form_field("button[@name='update']")

    def get_fields(self):
        return {
            'username':   self.get_username_input(),
            'email':      self.get_email_input(),
            'full_name': self.get_full_name_input(),
            'update':     self.get_update_button()
        }

    def submit_form(self):
        self.test.click_through(
            self.get_update_button(),
            self.test.BY_ALERT
        )

    def assert_profile_is_updated(self):
        self.test.assert_has_message(
            'alert',
            "Successfully updated profile information"
        )
