from .base import Page
from selenium.webdriver.common.by import By


class OrganizationPage(Page):
    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + '/organizations/{}/'

    def go_to(self, org):
        self.browser.get(self.url.format(org))
        self.test.wait_for(self.get_organization)
        return self

    def get_organization(self):
        return self.test.organization_name("org-logo")

    def get_organization_logo_alt_text(self):
        return self.get_organization().find_element_by_xpath(
            "//img[@class='org-logo']").get_attribute('alt')

    def get_container(self, xpath):
        return self.test.container(xpath)

    def get_org_description_and_members(self):
        return self.get_container(
            "//div[contains(@class, 'org-detail')]")

    def get_edit_button(self):
        more = self.browser.find_element_by_xpath(
            "//div[contains(@class, 'btn-more')]")
        self.test.click_through(
            more, (By.CSS_SELECTOR, "div.dropdown.pull-right.btn-more.open"))
        edit = self.get_container("//a[@class='edit']")
        self.test.click_through(edit, (By.CLASS_NAME, 'modal-backdrop'))

    def get_edit_modal_form(self, xpath):
        return self.test.form_field('edit-org', xpath)

    def get_name_input(self):
        return self.get_edit_modal_form("input[@name='name']")

    def get_description_input(self):
        return self.get_edit_modal_form("textarea[@name='description']")

    def get_urls_input(self):
        return self.get_edit_modal_form("input[@name='urls']")

    def get_submit(self):
        return self.get_edit_modal_form("button[@name='submit']")

    def get_fields(self):
        return {
            'name':        self.get_name_input(),
            'description': self.get_description_input(),
            'urls':        self.get_urls_input(),
            'add':         self.get_submit()
        }

    def get_close(self, xpath):
        return self.test.button_class("{}".format(xpath))

    def get_archive_button(self):
        more = self.browser.find_element_by_xpath(
            "//div[contains(@class, 'btn-more')]")
        self.test.click_through(
            more, (By.CSS_SELECTOR, "div.dropdown.pull-right.btn-more.open"))
        return self.get_container("//a[@class='archive']")

    def get_archive_final(self):
        return self.test.link("archive-final")

    def get_unarchive_final(self):
        return self.test.link("unarchive-final")

    def get_projects_table(self, xpath):
        return self.test.table_body("DataTables_Table_0", xpath)

    def get_project(self):
        return self.get_projects_table("//tr")

    def get_project_title(self):
        return self.browser.find_element_by_xpath(
            "//div[contains(@class, 'inner-header')]/h2").text

    def get_users_page(self):
        return self.browser.find_element_by_xpath(
            "//div[contains(@class, 'btn-view')]")

    def get_welcome_message(self):
        return self.get_container("//div[contains(@class, 'project-list')]")

    def get_new_project(self):
        return self.browser.find_element_by_xpath(
            "//a[@href='/projects/new/']")

    def get_add_members(self):
        return self.test.link("add-members")
