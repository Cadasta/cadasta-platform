from .base import Page


class OrganizationsPage(Page):
    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + '/organizations/'

    def go_to(self):
        self.browser.get(self.url)
        self.test.wait_for(self.get_table)
        return self

    def get_table(self):
        return self.test.table('DataTables_Table_0')

    def get_thead(self, xpath):
        return self.test.table_head('DataTables_Table_0', xpath)

    def get_table_head_row(self, xpath):
        return self.get_thead("//tr" + xpath)

    def get_th(self, xpath):
        return self.get_table_head_row("//th" + xpath)

    def get_name_sorter(self):
        return self.get_th("[1]")

    def get_project_sorter(self):
        return self.get_th("[2]")

    def get_table_body(self, xpath):
        return self.test.table_body('DataTables_Table_0', xpath)

    def get_table_row(self, xpath):
        return self.get_table_body("//tr" + xpath)

    def get_table_data(self, xpath):
        return self.get_table_row("//td" + xpath)

    def get_empty_table(self):
        return self.get_table_data("[contains(@class, 'dataTables_empty')]")

    def get_organization_titles(self):
        return self.get_table_data("//h4")

    def get_search_box(self):
        return self.test.search_box("DataTables_Table_0")

    def get_add_button(self):
        return self.test.link("add-org")

    def get_modal(self):
        return self.test.modal()

    def get_modal_form(self, xpath):
        return self.test.form_field(
            "modal-organization-add", xpath)

    def get_name_input(self):
        return self.get_modal_form("input[@name='name']")

    def get_description_input(self):
        return self.get_modal_form("textarea[@name='description']")

    def get_urls_input(self):
        return self.get_modal_form("input[@name='urls']")

    def get_submit(self):
        return self.get_modal_form("button[@name='submit']")

    def get_close(self, xpath):
        return self.test.link("{}".format(xpath))

    def get_fields(self):
        return {
            'name':        self.get_name_input(),
            'description': self.get_description_input(),
            'urls':        self.get_urls_input(),
            'add':         self.get_submit()
        }

    def get_organization(self):
        return self.test.organization_name("org-logo")

    def get_organization_logo_alt_text(self):
        return self.get_organization().find_element_by_xpath(
            "//img[@class='org-logo']").get_attribute('alt')

    def try_submit(self, err=None, ok=None):
        fields = self.get_fields()
        fields['add'].click()
        fields = self.get_fields()
        if err is not None:
            for f in err:
                try:
                    self.test.assert_has_error_list()
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
