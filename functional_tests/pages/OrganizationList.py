from .base import Page
from .Organization import OrganizationPage
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException


class OrganizationListPage(Page):
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
        self.test.click_through(button, wait)

    def get_table_headers(self, xpath):
        table_head = self.test.table('DataTables_Table_0')
        return table_head.find_element_by_xpath("//thead//tr//th" + xpath)

    def get_table_data(self, xpath, row):
        return self.test.table_body(
            "DataTables_Table_0", "//tr{}//td".format(row) + xpath)

    def get_organization_title_in_table(self, row="[1]"):
        return self.get_table_data("//h4", row).text

    def get_new_organization_title_in_table(self):
        return self.get_organization_title_in_table("[3]")

    def sort_table_by(self, order, col):
        order = "asc" if order == "ascending" else "desc"
        col = "[2]" if col == "organization" else "[3]"
        self.click_through(
            self.get_table_headers(col),
            (By.CLASS_NAME, 'sorting_{}'.format(order))
        )
        organization_title = self.get_organization_title_in_table()
        return organization_title

    def get_search_box(self):
        return self.test.search_box("DataTables_Table_0")

    def get_archive_filter(self, xpath):
        return self.browser.find_element_by_xpath(
            "//select[contains(@id, 'archive-filter')]" + xpath)

    def get_archive_option(self, option):
        return self.get_archive_filter(
            "//option[contains(@value, '{}')]".format(option))

    def click_archive_filter(self, option):
        option = self.get_archive_option(option)
        self.click_through(option, (By.CLASS_NAME, 'sorting_asc'))

    def click_add_button(self):
        add_button = self.test.link("add-org")
        self.click_through(add_button, (By.CLASS_NAME, 'modal-content'))

    def get_modal_form(self, xpath):
        return self.browser.find_element_by_xpath(
            "//form[@action='/organizations/new/']//" + xpath)

    def get_name_input(self):
        return self.get_modal_form("input[@name='name']")

    def get_description_input(self):
        return self.get_modal_form("textarea[@name='description']")

    def get_urls_input(self):
        return self.get_modal_form("input[@name='urls']")

    def get_submit(self):
        return self.get_modal_form("button[@name='submit']")

    def get_fields(self):
        return {
            'name':        self.get_name_input(),
            'description': self.get_description_input(),
            'urls':        self.get_urls_input(),
            'add':         self.get_submit()
        }

    def click_submit_button(self):
        fields = self.get_fields()
        self.click_through(
            fields['add'], OrganizationPage.BY_ORG_OVERVIEW
        )

    def click_close_button(self, button):
        cancel = self.test.link(button)
        self.test.click_through_close(
            cancel, (By.CLASS_NAME, 'modal-backdrop'))

    def fill_inputboxes(self):
        fields = self.get_fields()
        fields['name'].send_keys("Organization #3")
        fields['description'].send_keys("This should go away.")
        fields['urls'].send_keys("notstaying.com")

    def check_inputboxes(self):
        fields = self.get_fields()
        assert fields["name"].text == ""
        assert fields["description"].text == ""
        assert fields["urls"].text == ""

    def try_cancel_and_close(self):
        self.test.try_cancel_and_close(
            self.click_add_button,
            self.fill_inputboxes,
            self.check_inputboxes
        )

    def try_submit(self, err=None, ok=None):
        fields = self.get_fields()

        try:
            fields['add'].click()
        except ElementNotVisibleException:
            self.browser.execute_script(
                "return arguments[0].scrollIntoView();", fields['add'])
            fields['add'].click()

        fields = self.get_fields()
        if err is not None:
            for f in err:
                try:
                    assert self.test.assert_has_error_list()
                except:
                    raise AssertionError(
                        'Field "' + f + '" should have error, but does not'
                    )
        if ok is not None:
            for f in ok:
                try:
                    self.test.assert_field_has_no_error(fields[f])
                except:
                    raise AssertionError(
                        'Field "' + f + '" should not have error, but does'
                    )
