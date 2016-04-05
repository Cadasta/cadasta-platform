from .base import Page


class UsersPage(Page):
    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + '/users/'

    def go_to(self):
        """To access the user list page by a superuser"""
        self.browser.get(self.url)
        self.test.wait_for(self.get_h1_users)
        return self

    def get_h1_users(self):
        return self.browser.find_element_by_xpath(
            self.test.xpath('h1', 'Users')
        )
