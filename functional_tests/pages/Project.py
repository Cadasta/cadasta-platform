from .base import Page
from selenium.common.exceptions import NoSuchElementException


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

    def get_org_logo(self):
        try:
            url = self.BY_CSS('.org-logo img').get_attribute('src')
        except NoSuchElementException:
            url = ''
        return url

    def get_org_name(self):
        try:
            name = self.BY_CSS('.org-logo img').get_attribute('alt')
        except NoSuchElementException:
            name = self.BY_CSS('.org-logo h2').text
        return name

    def get_project_name(self):
        h2_elems = self.BYS_CSS('.inner-header h2')
        assert len(h2_elems) > 0
        return h2_elems[len(h2_elems) - 1].text

    def get_project_description(self):
        return self.BY_CSS('.desc p').text

    def check_page_contents(self, target_project):
        """This checks that the page displays the correct project data
        based on the supplied test data for a project."""

        assert self.get_org_name() == target_project['_org_name']
        assert self.get_org_logo() == target_project['_org_logo']
        assert self.get_project_name() == target_project['name']
        assert self.get_project_description() == target_project['description']
