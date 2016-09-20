from .base import Page
from selenium.webdriver.common.by import By


class OrganizationMemberPage(Page):
    BY_ORG_MEMBERS = (By.CLASS_NAME, 'page-title')

    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + '/organizations/'

    def go_to(self):
        self.browser.get(self.url)
        self.test.wait_for(self.get_org_list_title)
        return self

    def get_org_list_title(self):
        title = self.test.page_title()
        assert title.text == "Organizations".upper()
        return title

    def click_through(self, button, wait):
        return self.test.click_through(button, wait)

    def get_table_row(self, xpath=""):
        return self.test.table_body('DataTables_Table_0', "//tr" + xpath)

    def get_member_title(self):
        return self.test.page_content("//h2").text

    def go_to_testuser_member_page(self, success=True):
        testuser_page = self.get_table_row(
            "[contains(@onclick, '/testuser/')]"
        )
        if success:
            self.click_through(testuser_page, (By.CLASS_NAME, 'page-title'))
            testuser_title = self.get_member_title()
            return testuser_title
        else:
            self.click_through(testuser_page, (By.CLASS_NAME, 'alert-warning'))

    def go_to_admin_member_page(self):
        testuser_page = self.get_table_row(
            "[contains(@onclick, '/admin_user/')]"
        )
        self.click_through(testuser_page, (By.CLASS_NAME, 'page-title'))
        testuser_title = self.get_member_title()
        return testuser_title

    def get_form_field(self, xpath):
        return self.test.form_field(
                'org-member-edit', xpath)

    def get_displayed_member_info(self):
        return self.get_form_field("div[contains(@class, 'member-info')]")

    def get_member_role_select(self, xpath):
        return self.get_form_field(
            "select[contains(@id, 'id_org_role')]" + xpath
        )

    def get_member_role_option(self):
        return self.get_member_role_select("//option[contains(@value, 'M')]")

    def get_admin_role_option(self):
        return self.get_member_role_select("//option[contains(@value, 'A')]")

    def get_org_role_error(self):
        return self.get_form_field("div[contains(@class, 'member-role')]" +
                                   "//ul[contains(@class, 'errorlist')]")

    def get_selected_role(self):
        return self.get_member_role_select(
            "//option[contains(@selected, 'selected')]")

    def get_role_options(self):
        return {
            "member": self.get_member_role_option(),
            "admin": self.get_admin_role_option(),
            "selected": self.get_selected_role()
        }

    def click_submit_button(self):
        self.click_through(
            self.test.button("submit"), self.BY_ORG_MEMBERS
        )

    def click_remove_button(self):
        self.click_through(
            self.test.button("remove"), (By.CSS_SELECTOR, "div.modal.fade.in")
        )

    def click_disabled_remove_button(self):
        self.test.click_through_close(
            self.test.button("remove"), (By.CSS_SELECTOR, "div.modal.fade.in")
        )

    def click_remove_member_and_confirm_buttons(self):
        self.click_remove_button()
        self.click_through(
            self.test.link("confirm"), self.BY_ORG_MEMBERS
        )

    def try_cancel_and_close(self):
        self.test.try_cancel_and_close_confirm_modal(
            self.click_remove_button
        )

    def get_project_permission(self, xpath):
        return self.test.table_body("projects-permissions", '//select' + xpath)

    def get_project_user(self):
        return self.get_project_permission("//option[contains(@value, 'PU')]")

    def get_data_collector(self):
        return self.get_project_permission("//option[contains(@value, 'DC')]")

    def get_project_manager(self):
        return self.get_project_permission("//option[contains(@value, 'PM')]")

    def get_public_user(self):
        return self.get_project_permission("//option[contains(@value, 'Pb')]")

    def get_selected_permission(self):
        return self.get_project_permission(
            "//option[contains(@selected, 'selected')]")

    def get_permission_options(self):
        return {
            'pu':       self.get_project_user(),
            'dc':       self.get_data_collector(),
            'pm':       self.get_project_manager(),
            'pb':       self.get_public_user(),
            'selected': self.get_selected_permission()
        }
