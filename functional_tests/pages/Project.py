from .base import Page
from selenium.webdriver.common.by import By


class ProjectPage(Page):
    def __init__(self, test, org_slug, project_slug):
        super().__init__(test)
        self.path = '/organizations/{}/projects/{}/'.format(
            org_slug, project_slug
        )
        self.url = self.base_url + self.path

        # TODO: This may be refactored as common code into Page class
        self.BY_CSS = test.browser.find_element_by_css_selector
        self.BYS_CSS = test.browser.find_elements_by_css_selector

    def is_on_page(self):
        """Returns True if user is on this page"""
        return self.test.get_url_path() == self.path

    def go_to(self):
        self.browser.get(self.url)
        return self

    def get_page_header(self, xpath):
        return self.test.page_header(xpath)

    def click_through(self, button, wait, screenshot=None):
        return self.test.click_through(button, wait, screenshot)

    def click_through_close(self, button, wait):
        return self.test.click_through_close(button, wait)

    def get_org_name(self):
        return self.BY_CSS('.org-name').text

    def get_project_name(self):
        project_name = self.test.page_title().text
        project_name = project_name.replace(self.get_org_name(), '')
        project_name = project_name.replace('\n', '')
        return project_name

    def get_project_description(self):
        return self.BY_CSS('.detail p').text

    def check_page_contents(self, target_project):
        """This checks that the page displays the correct project data
        based on the supplied test data for a project."""

        assert self.get_org_name() == target_project['_org_name']
        assert self.get_project_name() == target_project['name'].upper()
        assert self.get_project_description() == target_project['description']

    # START OF ARCHIVE TESTS
    def click_on_close_alert_button(self):
        close = self.browser.find_element_by_xpath(
            "//div[contains(@class, 'alert')]" +
            "//button[contains(@class, 'close')]")
        self.click_through_close(close, self.test.BY_ALERT)

    def click_on_edit_button(self, success=True):
        self.click_on_content_more_button()
        button = self.test.page_content(
            "//ul[contains(@class, 'dropdown-menu')]" +
            "//a[contains(@href, '/edit/')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    def click_on_delete_button(self, success=True):
        self.click_on_content_more_button()
        button = self.test.page_content(
            "//ul[contains(@class, 'dropdown-menu')]" +
            "//a[contains(@href, '/delete/')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    def click_on_add_button(self, location, success=True):
        button = self.test.page_content(
            "//div[contains(@class, '{}')]".format(location) +
            "//a[contains(@class, 'btn-primary')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    def click_on_detach_resource_button(self, location, success=True):
        button = self.test.page_content(
            "//div[contains(@class, '{}')]".format(location) +
            "//button[contains(@class, 'btn-danger')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    # MAIN PROJECT HEADER BUTTONS
    def click_on_add_location_button(self, success=True):
        button = self.browser.find_element_by_xpath(
            "//a[contains(@href, '/locations/new/')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    def click_on_add_resource_button_from_dropdown(self, success=True):
        button = self.get_page_header(
            "//div//button[contains(@class, 'dropdown-toggle')]")
        self.click_through(button, (By.CLASS_NAME, "open"))
        button = self.browser.find_element_by_xpath(
            "//a[contains(@href, '/resources/add/')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    def click_on_header_more_button(self):
        more = self.get_page_header(
                "//div[contains(@class, 'btn-more')]")
        self.click_through(
            more, (By.CSS_SELECTOR, "div.dropdown.pull-right.btn-more.open"))

    def click_on_edit_boundary_button(self, location, success=True):
        self.click_on_header_more_button()
        button = self.get_page_header(
            "//a[contains(@href, '/edit/{}/')]".format(location))
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    # SPATIAL UNIT PAGE
    def click_on_location(self):
        button = self.browser.find_element_by_xpath(
            "//*[contains(@class, 'leaflet-clickable')]")
        self.click_through(button, (By.CLASS_NAME, 'leaflet-popup'))
        button = self.browser.find_element_by_xpath(
            "//div[contains(@class, 'leaflet-popup')]" +
            "//a[contains(@href, 'records/locations')]")
        self.click_through(button, (By.CLASS_NAME, 'tab-content'))

    def click_on_content_more_button(self):
        button = self.test.page_content("//div[contains(@class, ' btn-more')]")
        self.click_through(
            button, (By.CSS_SELECTOR, "div.dropdown.pull-right.btn-more.open"))

    # SPATIAL UNIT RESOURCES TAB
    def click_on_location_resource_tab(self):
        button = self.test.page_content("//a[@href='#resources']")
        self.click_through(
            button, (By.CSS_SELECTOR, "div.tab-pane.active#resources"))

    # SPATIAL UNIT RELATIONSHIPS TAB
    def click_on_location_relationship_tab(self):
        button = self.test.page_content("//a[@href='#relationships']")
        self.click_through(
            button, (By.CSS_SELECTOR, "div.tab-pane.active#relationships"))

    def click_on_relationship_in_table(self):
        button = self.test.table_body(
            "DataTables_Table_0", "//tr[contains(@class, 'linked')]")
        self.test.click_through_close(button, (By.CLASS_NAME, 'nav-tabs'))

    # PARTY PAGE
    def click_on_party_in_table(self):
        button = self.test.table_body(
            "DataTables_Table_0", "//tr//a")
        self.test.click_through_close(
            button, (By.CLASS_NAME, 'leaflet-container'))

    # RESOURCES PAGE
    def click_on_resources_tab(self):
        button = self.browser.find_element_by_xpath(
            "//div[@id='sidebar']//li[@class='resources']")
        self.click_through(button, (By.CLASS_NAME, 'resources'))
        assert self.test.page_content(
            "//div[@class='page-title']").text == 'RESOURCES'

    def get_resource_in_table(self, xpath=''):
        return self.browser.find_element_by_xpath(
            "//tr[contains(@class, 'linked-resource')]" + xpath)

    def click_on_resource_in_table(self):
        button = self.get_resource_in_table()
        self.click_through(button, (By.CLASS_NAME, 'resources'))
        assert self.test.page_content(
            "//div[@class='page-title']").text == 'RESOURCE DETAIL'

    def click_on_edit_resource_button(self, success=True):
        button = self.browser.find_element_by_xpath(
            "//ul[contains(@class, 'resource-actions')]" +
            "//a[contains(@href, 'edit')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()

    def click_on_delete_resource_button_and_confirm(self, success=True):
        button = self.browser.find_element_by_xpath(
            "//ul[contains(@class, 'resource-actions')]" +
            "//a[contains(@href, 'delete')]")
        self.click_through(button, (By.CSS_SELECTOR, "div.modal.fade.in"))
        button = self.browser.find_element_by_xpath(
            "//a[contains(@class, 'archive-final')]")
        if success:
            # Finish writing this
            assert False
        else:
            self.click_through(button, self.test.BY_ALERT)
            self.click_on_close_alert_button()
