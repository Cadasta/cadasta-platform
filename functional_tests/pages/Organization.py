from .base import Page
from selenium.webdriver.common.by import By


class OrganizationPage(Page):
    BY_MODAL_FADE = (By.CSS_SELECTOR, "div.modal.fade.in")
    BY_MODAL_BACKDROP = (By.CLASS_NAME, 'modal-backdrop')
    BY_ORG_OVERVIEW = (
        By.XPATH, "//h2[normalize-space(.)='Organization Overview']"
    )

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

    def click_through(self, button, wait, screenshot=None):
        return self.test.click_through(button, wait, screenshot)

    def click_through_close(self, button, wait):
        return self.test.click_through_close(button, wait)

    def get_container(self, xpath):
        return self.test.container(xpath)

    def get_page_header(self, xpath):
        return self.test.page_header(xpath)

    def get_page_content(self, xpath):
        return self.test.page_content(xpath)

    def get_table_row(self, xpath=""):
        return self.test.table_body('DataTables_Table_0', "//tr" + xpath)

    def go_to_organization_page(self, new=False):
        row = "[2]" if new else "[1]"
        org_page = self.get_table_row(row)
        self.click_through(org_page, self.BY_ORG_OVERVIEW)

    def get_org_description_and_members(self):
        return self.get_page_content(
            "//div[contains(@class, 'detail')]").text

    def click_on_more_button(self):
        more = self.get_page_header(
                "//div[contains(@class, 'btn-more')]")
        self.click_through(
            more, (By.CSS_SELECTOR, "div.dropdown.pull-right.btn-more.open"))

    def click_on_edit_button(self, success=True):
        self.click_on_more_button()
        edit = self.get_page_header("//a[@class='edit']")
        if success:
            self.test.click_through(edit, self.BY_MODAL_BACKDROP)
        else:
            self.click_through(edit, (By.CLASS_NAME, 'alert-warning'))

    def get_edit_modal_form(self, xpath):
        return self.test.form_field('edit-org', xpath)

    def get_name_input(self):
        return self.get_edit_modal_form("input[@name='name']")

    def get_description_input(self):
        return self.get_edit_modal_form("textarea[@name='description']")

    def get_urls_input(self):
        return self.get_edit_modal_form("input[@name='urls']")

    def click_on_submit_button(self):
        submit = self.get_edit_modal_form("button[@name='submit']")
        self.click_through(submit, self.BY_ORG_OVERVIEW)

    def get_fields(self):
        return {
            'name':        self.get_name_input(),
            'description': self.get_description_input(),
            'urls':        self.get_urls_input(),
        }

    def fill_inputboxes(self):
        fields = self.get_fields()
        fields['name'].clear()
        fields['name'].send_keys("Evil Coorporation")
        fields['description'].clear()
        fields['description'].send_keys("Planning world domination.")
        fields['urls'].clear()
        fields['urls'].send_keys("notstaying.com")

    def check_inputboxes(self):
        fields = self.get_fields()
        assert fields["name"].get_attribute('value') == "Organization #0"
        assert fields["description"].text == "This is a test."
        assert fields["urls"].text == ""

    def try_cancel_and_close(self):
        self.test.try_cancel_and_close(
            self.click_on_edit_button,
            self.fill_inputboxes,
            self.check_inputboxes
        )

    def get_archive_container(self):
        return self.get_page_header("//a[@class='archive']")

    def get_archive_button(self):
        self.click_on_more_button()
        return self.get_archive_container()

    def click_on_archive_and_confirm(self, unarchive=False, final_check=False):
        archive = self.get_archive_container()
        self.click_through(archive, self.BY_MODAL_FADE)

        final = "unarchive-final" if unarchive else "archive-final"
        final = self.test.link(final)
        self.click_through_close(final, self.BY_MODAL_FADE)
        if final_check:
            return self.get_archive_button().text

    def click_on_close_alert_button(self):
        close = self.browser.find_element_by_xpath("//div[contains(@class, 'alert')]//button[contains(@class, 'close')]")
        self.click_through_close(close, (By.CLASS_NAME, 'alert-warning'))

    def get_add_project_button(self):
        return self.browser.find_element_by_xpath("//a[contains(@href, '/projects/new/')]")

    def click_on_add_project_button(self, success=False):
        button = self.get_add_project_button()
        if success:
            self.test.click_through(button, self.BY_MODAL_BACKDROP)
        else:
            self.click_through(button, (By.CLASS_NAME, 'alert-warning'))

    def try_cancel_and_close_archive(self):
        close_buttons = ["cancel", "close"]
        for close in close_buttons:
            archive = self.get_archive_button()
            assert "Archive" in archive.text

            self.click_through(archive, self.BY_MODAL_FADE)

            cancel = self.test.button_class(close)
            self.click_through_close(cancel, self.BY_MODAL_BACKDROP)

    def get_view_all_button(self):
        return self.get_page_content(
            "//div[contains(@class, 'detail')]//a"
            "[contains(./text(), 'View all')]")

    def click_on_view_all_button(self, successful=True):
        view_all = self.get_view_all_button()

        if not successful:
            self.click_through(view_all, (By.CLASS_NAME, 'panel-default'))
        else:
            self.test.click_through_close(view_all, (By.CLASS_NAME, 'detail'))
            view_all = self.get_page_content("//h2").text
            return view_all

    def click_on_project(self):
        project = self.get_table_row("[1]")
        self.click_through(project, (By.CLASS_NAME, "leaflet-container"))
        project_title = self.test.page_title()
        return project_title.text

    def get_welcome_message(self):
        return self.get_page_content(
            "//div[contains(@class, 'panel-body')]").text

    def click_add_new_project_button(self):
        new_proj = self.get_page_content(
            "//a[contains(@href, '/projects/new/')]")
        self.click_through(new_proj, (By.CLASS_NAME, 'new-project-page'))
        title = self.test.h1("new-project-page").text
        return title

    def go_back_to_organization_list(self):
        back_button = self.test.link('index-link')
        self.click_through(back_button, (By.CLASS_NAME, 'add-org'))

    def get_archived_project_filter(self):
        return self.browser.find_element_by_xpath(
            "//select[contains(@id, 'archive-filter')]" + xpath)

    def get_archive_option(self, option):
        return self.get_archive_filter(
            "//option[contains(@value, '{}')]".format(option))

    def click_archive_filter(self, option):
        option = self.get_archive_option(option)
        self.test.click_through(option, (By.CLASS_NAME, 'sorting_asc'))
