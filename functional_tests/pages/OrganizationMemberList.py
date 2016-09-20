from .base import Page
from selenium.webdriver.common.by import By


class OrganizationMemberListPage(Page):
    BY_MODAL_BACKDROP = (By.CLASS_NAME, 'modal-backdrop')

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

    def get_page_content(self, xpath):
        return self.test.page_content(xpath)

    def go_to_member_list_page(self):
        view_all = self.get_page_content(
            "//div[contains(@class, 'detail')]//a"
            "[contains(./text(), 'View all')]")
        self.click_through(
            view_all, (By.CLASS_NAME, 'page-title')
        )
        title = self.get_page_content("//h2").text
        return title

    def click_on_add_button(self, success=True):
        add_button = self.get_page_content("//a[contains(@href, '/add/')]")
        if success:
            self.click_through(add_button, self.BY_MODAL_BACKDROP)
        else:
            self.click_through(add_button, (By.CLASS_NAME, 'alert-warning'))

    def get_modal(self, xpath):
        return self.browser.find_element_by_xpath(
            "//div[contains(@class, 'modal-content')]" + xpath
        )

    def click_on_input(self):
        return self.get_modal(
            "//input[@type='text']"
        )

    def click_submit_button(self, success=True):
        submit_button = self.get_modal(
                            "//button[@type='submit']")
        if not success:
            self.click_through(submit_button, (By.CLASS_NAME, 'errorlist'))
            error_list = self.test.assert_has_error_list()
            return error_list.text
        else:
            self.test.click_through_close(
                submit_button, self.BY_MODAL_BACKDROP)
            return self.get_page_content("//h2").text

    def fill_form(self):
        input_box = self.click_on_input()
        input_box.send_keys("This should go away.")

    def test_empty_form(self):
        input_box = self.click_on_input()
        assert input_box.text == ""

    def try_cancel_and_close(self):
        self.test.try_cancel_and_close(
            self.click_on_add_button,
            self.fill_form,
            self.test_empty_form)
