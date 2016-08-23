from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from .base import Page
from django_countries import countries


class ProjectListPage(Page):

    path = '/projects/'

    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + self.path

    def is_on_page(self):
        """Returns True if user is on this page"""
        return self.test.get_url_path() == self.path

    def go_to(self):
        self.browser.get(self.url)

    def go_to_and_check_on_page(self):
        self.browser.get(self.url)
        assert self.is_on_page()

    def is_list_empty(self):
        cell = self.browser.find_element_by_xpath(
            "//table[@id='DataTables_Table_0']/tbody/tr/td"
        )
        return (cell.text == "No data available in table")

    def check_project_list(self, projects):
        """This verifies that the supplied list of projects
        and only these projects are visible on the page """

        rows = self.browser.find_elements_by_xpath(
            "//table[@id='DataTables_Table_0']/tbody/tr"
        )
        assert len(rows) == len(projects)
        for row in rows:
            onclick_items = row.get_attribute('onclick').split('/')
            project_slug = onclick_items[4]

            cells = row.find_elements_by_tag_name('td')
            actual_org_slug = onclick_items[2]
            try:
                img = cells[2].find_element_by_tag_name('img')
                actual_org_logo = img.get_attribute('src')
                actual_org_name = img.get_attribute('alt')
            except NoSuchElementException:
                actual_org_logo = None
                alt = cells[2].find_elements_by_class_name('org-name-alt')
                actual_org_name = alt[0].text
            actual_project_name = (
                cells[1].find_element_by_tag_name('h4').text
            )
            actual_project_description = (
                cells[1].find_element_by_tag_name('p').text
            )
            actual_country = cells[3].text

            target_project = None
            for project in projects:
                if project['slug'] == project_slug:
                    target_project = project
                    break
            assert target_project

            assert actual_org_slug == target_project['_org_slug']
            assert actual_org_name == target_project['_org_name']
            expected_org_logo = (
                target_project['_org_logo']
                if target_project['_org_logo']
                else None
            )
            assert actual_org_logo == expected_org_logo
            assert actual_project_name == target_project['name']
            assert actual_project_description == target_project['description']
            expected_country = (
                dict(countries)[target_project['country']]
                if target_project['country'] else ''
            )
            assert actual_country == expected_country

            # TODO Check also last updated column

    def get_table_headers(self, xpath):
        table_head = self.test.table('DataTables_Table_0')
        return table_head.find_element_by_xpath("//thead//tr//th" + xpath)

    def get_table_data(self, xpath, row):
        return self.test.table_body(
            "DataTables_Table_0", "//tr{}//td".format(row) + xpath)

    def get_project_title_in_table(self, row="[1]"):
        return self.get_table_data("//h4", row).text

    def sort_table_by(self, order):
        order = "asc" if order == "ascending" else "desc"
        self.test.click_through(
            self.get_table_headers("[2]"),
            (By.CLASS_NAME, 'sorting_{}'.format(order))
        )
        project_title = self.get_project_title_in_table()
        return project_title

    def get_archive_filter(self, xpath):
        return self.browser.find_element_by_xpath(
            "//select[contains(@id, 'archive-filter')]" + xpath)

    def get_archive_option(self, option):
        return self.get_archive_filter(
            "//option[contains(@value, '{}')]".format(option))

    def click_archive_filter(self, option):
        option = self.get_archive_option(option)
        self.test.click_through(option, (By.CLASS_NAME, 'sorting_asc'))
