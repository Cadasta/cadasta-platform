from .base import Page


class RegistrationPage(Page):

    path = '/account/signup/'

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
        return self.test.form('account-register')

    def get_form_field(self, xpath):
        return self.test.form_field('account-register', xpath)

    def get_username_input(self):
        return self.get_form_field("input[@name='username']")

    def get_email_input(self):
        return self.get_form_field("input[@name='email']")

    def get_password_input(self):
        return self.get_form_field("input[@name='password']")

    def get_full_name_input(self):
        return self.get_form_field("input[@name='full_name']")

    def get_register_button(self):
        return self.get_form_field("button[@name='register']")

    def get_fields(self):
        return {
            'username':   self.get_username_input(),
            'email':      self.get_email_input(),
            'password':   self.get_password_input(),
            'full_name':  self.get_full_name_input(),
            'register':   self.get_register_button()
        }

    def setup(self, values):
        """Go to registration page and set up selected fields."""
        self.go_to()
        fields = self.get_fields()
        for k, v in values:
            fields[k].send_keys(v)
        return fields['register']

    def register(self, values):
        self.test.click_through(self.setup(values), self.test.BY_DASHBOARD)

    def try_submit(self, err=None, ok=None, message=None):
        fields = self.get_fields()
        sel = self.test.BY_ALERT if err is None else self.test.BY_FIELD_ERROR
        self.test.click_through(fields['register'], sel, screenshot='tst')
        fields = self.get_fields()
        if err is not None:
            for f in err:
                try:
                    self.test.assert_field_has_error(fields[f], message)
                except AssertionError:
                    raise AssertionError('Field "' + f +
                                         '" should have error, but does not')
        if ok is not None:
            for f in ok:
                try:
                    self.test.assert_field_has_no_error(fields[f])
                except AssertionError:
                    raise AssertionError('Field "' + f +
                                         '" should not have error, but does')
