from .base import Page
from selenium.webdriver.common.by import By


class UsersPage(Page):

    path = '/users/'

    # XPath to unambiguously search for the row for
    # the user with the specified username
    row_xpath = (
        "//table[@id='DataTables_Table_0']/tbody" +
        "/tr[./td[1]/p[1][text()='{0}']]"
    )

    # XPath to unambiguously search for the form that
    # (de)activates the user with the specified username.
    # The '{x}' are as follows:
    #  {0} - username
    #  {1} - action (either 'deactivate/' if active or
    #        'activate/' if inactive); set to '' if don't care
    form_xpath = (
        row_xpath +
        "/td[5]/form[starts-with(@action,'/users/{0}/{1}')]"
    )

    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + self.path

    def is_on_page(self):
        """Returns True if user is on this page"""
        return self.test.get_url_path() == self.path

    def go_to(self):
        """To access the user list page by a superuser"""
        self.browser.get(self.url)
        self.get_h1_users()
        return self

    def get_h1_users(self):
        # The following is not localized (#l10n)
        return self.browser.find_element_by_xpath(
            "//h1[text()='Users' and not(*[2])]"
        )

    def get_num_users(self):
        xpath = "//table[@id='DataTables_Table_0']/tbody/tr"
        rows = self.browser.find_elements_by_xpath(xpath)
        return len(rows)

    def get_de_activate_user_url(self, is_activate, username):
        return "{}/users/{}/{}/".format(
            self.test.live_server_url, username,
            ('activate' if is_activate else 'deactivate'),
        )

    def get_activate_user_url(self, username):
        return self.get_de_activate_user_url(True, username)

    def get_deactivate_user_url(self, username):
        return self.get_de_activate_user_url(False, username)

    def go_to_activate_user_url(self, username):
        self.browser.get(self.get_activate_user_url(username))

    def go_to_deactivate_user_url(self, username):
        self.browser.get(self.get_deactivate_user_url(username))

    def get_de_activate_user_form(self, username):
        formatted_xpath = self.form_xpath.format(username, '')
        form = self.browser.find_element_by_xpath(formatted_xpath)
        return form

    def is_user_active(self, username):
        """Returns whether the specified user is active or not as stated in
        Users Management UI by inspecting the (de)activate form and button.
        This method also checks that the form action URL is valid and
        if the form button label matches the URL."""

        form = self.get_de_activate_user_form(username)
        action = form.get_attribute('action').split('/')[5]  # Full URL
        assert (action == 'activate') or (action == 'deactivate')
        button = form.find_element_by_xpath("button")
        action_label = button.text
        # The following is not localized (#l10n)
        assert action.capitalize() == action_label
        return action == 'deactivate'

    def click_de_activate_button(self, username):
        form = self.get_de_activate_user_form(username)
        button = form.find_element_by_xpath("button")
        action = form.get_attribute('action').split('/')[5]  # Full URL
        new_action = 'activate/' if action == 'deactivate' else 'deactivate/'
        formatted_xpath = self.form_xpath.format(username, new_action)
        self.test.click_through(button, (By.XPATH, formatted_xpath))

    def get_user_cell_value(self, username, cell_pos):
        formatted_xpath = self.row_xpath.format(username)
        user_row = self.browser.find_element_by_xpath(formatted_xpath)
        cell_xpath = "./td[{}]".format(cell_pos)
        cell = user_row.find_element_by_xpath(cell_xpath)
        return cell.text

    def get_user_name(self, username):
        return self.get_user_cell_value(username, 1)

    def get_user_email(self, username):
        return self.get_user_cell_value(username, 2)

    def get_user_orgs(self, username):
        return self.get_user_cell_value(username, 3)

    def get_user_last_login(self, username):
        return self.get_user_cell_value(username, 4)
