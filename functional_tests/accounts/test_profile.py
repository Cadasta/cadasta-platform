from base import FunctionalTest
from pages.Profile import ProfilePage
from pages.Login import LoginPage
from accounts.tests.factories import UserFactory


class ProfileTest(FunctionalTest):
    def setUp(self):
        UserFactory.create(username='user1', password='user1pwd')

    def test_profile_view_and_edit(self):
        """A registered user can view and edit their profile."""
        LoginPage(self).login('user1', 'user1pwd')

        page = ProfilePage(self)
        page.go_to()
        fields = page.get_fields()

        fields['first_name'].clear()
        fields['first_name'].send_keys('Kenny')
        fields['last_name'].clear()
        fields['last_name'].send_keys('Everett')
        self.click_through(fields['update'], self.BY_ALERT)
        self.assert_has_message('alert',
                                "Successfully updated profile information")

        self.click_through(
            self.browser.find_element_by_xpath("//a[.='Logout']"),
            self.BY_ALERT
        )
        self.assert_has_message('alert', "logged out")
        LoginPage(self).login('user1', 'user1pwd')

        page = ProfilePage(self)
        page.go_to()
        fields = page.get_fields()
        assert fields['first_name'].get_attribute('value') == 'Kenny'
        assert fields['last_name'].get_attribute('value') == 'Everett'
