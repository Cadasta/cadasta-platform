from selenium.common.exceptions import NoSuchElementException

from .base import Page


class DashboardPage(Page):

    path = '/dashboard/'

    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + self.path

    def is_on_page(self):
        """Returns True if user is on this page"""
        return self.test.get_url_path() == self.path

    def go_to(self):
        self.browser.get(self.url)
        return self

    def get_dashboard_map(self):
        return self.browser.find_element_by_id('dashboard-map')

    def has_nav_link(self, title):
        try:
            return self.browser.find_element_by_xpath(
                '//nav'
            ).find_element_by_link_text(title)
        except NoSuchElementException:
            return None
