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
        return self.get_form_field("input[@name='password1']")

    def get_password_repeat_input(self):
        return self.get_form_field("input[@name='password2']")

    def get_full_name_input(self):
        return self.get_form_field("input[@name='full_name']")

    def get_register_button(self):
        return self.get_form_field("button[@name='register']")

    def get_fields(self):
        return {
            'username':   self.get_username_input(),
            'email':      self.get_email_input(),
            'password1':  self.get_password_input(),
            'password2':  self.get_password_repeat_input(),
            'full_name': self.get_full_name_input(),
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
        self.test.click_through(self.setup(values),
                                self.test.BY_ALERT)

    def try_submit(self, err=None, ok=None):
        fields = self.get_fields()
        fields['register'].click()
        fields = self.get_fields()
        if err is not None:
            for f in err:
                try:
                    self.test.assert_field_has_error(fields[f])
                except:
                    raise AssertionError('Field "' + f +
                                         '" should have error, but does not')
        if ok is not None:
            for f in ok:
                try:
                    self.test.assert_field_has_no_error(fields[f])
                except:
                    raise AssertionError('Field "' + f +
                                         '" should not have error, but does')
