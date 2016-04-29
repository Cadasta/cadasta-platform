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

    def go_to_member_list_page(self):
        view_all = self.browser.find_element_by_xpath(
            "//div[contains(@class, 'btn-view')]")
        self.click_through(
            view_all, (By.CLASS_NAME, 'page-title')
        )
        title = self.test.page_title().text
        return title

    def click_on_add_button(self):
        add_button = self.test.container("//a[contains(@href, '/add/')]")
        self.click_through(add_button, self.BY_MODAL_BACKDROP)

    def click_on_input(self):
        return self.browser.find_element_by_xpath(
            "//input[@id='id_identifier']"
        )

    def click_submit_button(self, success=True):
        submit_button = self.browser.find_element_by_xpath(
                            "//button[@type='submit']")
        if not success:
            self.click_through(submit_button, (By.CLASS_NAME, 'errorlist'))
            error_list = self.test.assert_has_error_list()
            return error_list.text
        else:
            self.test.click_through_close(
                submit_button, self.BY_MODAL_BACKDROP)
            return self.test.page_title().text

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
