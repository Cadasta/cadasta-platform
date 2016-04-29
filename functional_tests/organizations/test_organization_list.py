from base import FunctionalTest
from pages.OrganizationList import OrganizationListPage
from pages.Organization import OrganizationPage
from pages.Login import LoginPage

from accounts.tests.factories import UserFactory


class OrganizationListTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        self.add_all_test_data()
        UserFactory.create(
            username='wyldstyle',
            password='password')

    def test_organizations_view_without_permission(self):
        """ Unregistered users cannot see organizations."""

        page = OrganizationListPage(self)
        page.go_to()

        empty_table = page.get_empty_table()
        assert empty_table == 'No data available in table'

    def test_organizations_view_with_permission(self):
        """A registered user can view organizations"""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationListPage(self)
        page.go_to()

        organization_title = page.get_organization_title_in_table()
        assert organization_title == 'Organization #0'

    def test_sorting_organization_view(self):
        """A registered user user can sort the organization list
        by id, name, and number of projects."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationListPage(self)
        page.go_to()

        first_org = page.sort_table_by("descending", col="organization")
        assert first_org == 'Organization #1'

        first_org = page.sort_table_by("ascending", col="organization")
        assert first_org == 'Organization #0'

        first_org = page.sort_table_by("ascending", col="project")
        assert first_org == 'Organization #1'

        first_org = page.sort_table_by("descending", col="project")
        assert first_org == 'Organization #0'

    def test_searching_for_organizations(self):
        """A registered user user can search for organization by name."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationListPage(self)
        page.go_to()

        search = page.get_search_box()
        search.send_keys("#1")

        organization_title = page.get_organization_title_in_table()
        assert organization_title == 'Organization #1'

    def test_adding_an_organization(self):
        """A registered user can add an organization
        and this organization if visible to other users."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationListPage(self)
        page.go_to()

        page.click_add_button()
        page.try_cancel_and_close()

        fields = page.get_fields()
        page.try_submit(err=['name'], ok=['description', 'urls'])

        fields = page.get_fields()
        fields['name'].send_keys('Organization #2')
        fields['description'].send_keys('This is a test organization')
        fields['urls'].send_keys('test.com')
        page.try_submit(err=['urls'], ok=['name', 'description', 'urls'])

        fields = page.get_fields()
        fields['urls'].clear()

        page.click_submit_button()
        organization_name = OrganizationPage(self).get_organization_title()
        assert organization_name == 'Organization #2'
        self.logout()

        LoginPage(self).login('wyldstyle', 'password')
        page = OrganizationListPage(self)
        page.go_to()

        organization_table = page.get_new_organization_title_in_table()
        assert "Organization #2" in organization_table
