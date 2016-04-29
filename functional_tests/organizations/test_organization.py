from base import FunctionalTest
from pages.Organization import OrganizationPage
from pages.Login import LoginPage

from organization.models import OrganizationRole
from accounts.tests.factories import UserFactory


class OrganizationTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        orgs = self.add_all_test_data()
        OrganizationRole.objects.create(
                organization=orgs[0],
                user=UserFactory.create(
                        username='admin_user',
                        password='password'),
                admin=True)

    def test_organization_view(self):
        """A registered user can view an organization's dashboard.
           Org description and users are displayed."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        info = page.get_org_description_and_members()
        assert "This is a test." in info
        assert "Test User" in info
        assert "Username: testuser" in info
        self.logout()

        LoginPage(self).login('testuser', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        info = page.get_org_description_and_members()
        assert "This is a test." in info
        assert "Test User" in info
        assert "Username: testuser" in info

    def test_edit_organization(self):
        """A registered admin user can edit an organization's information,
        but a regular user cannot"""
        LoginPage(self).login('testuser', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        page.click_on_edit_button(success=False)
        self.logout()

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        page.click_on_edit_button()
        page.try_cancel_and_close()

        fields = page.get_fields()
        assert fields["name"].get_attribute("value") == "Organization #0"
        assert fields["description"].text == "This is a test."
        assert fields["urls"].text == ""

        fields["name"].clear()
        fields["name"].send_keys("Stark Enterprise")
        fields["description"].clear()
        fields["description"].send_keys("A technology company.")
        page.click_on_submit_button()

        name = page.get_organization_title()
        info = page.get_org_description_and_members()
        assert "Stark Enterprise" in name
        assert "A technology company." in info

    def test_archiving_organization(self):
        """A registered admin user can archive/unarchive an organization,
        but a regular member can't."""
        LoginPage(self).login('testuser', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        page.get_archive_button()

        archive = page.click_on_archive_and_confirm()
        assert archive == "Archive organization"
        self.logout()

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        page.try_cancel_and_close_archive()
        page.get_archive_button()

        archive = page.click_on_archive_and_confirm()
        assert archive == "Unarchive organization"

        archive = page.click_on_archive_and_confirm(unarchive=True)
        assert archive == "Archive organization"

    def test_getting_to_the_user_list(self):
        """A registered admin user can view an organization's member list,
        but a regular member can't."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        page.click_on_view_all_button(successful=False)
        url = self.get_url_path()
        assert "members" not in url
        self.logout()

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        title = page.click_on_view_all_button()
        assert title == "Members".upper()

    def test_navigating_to_project_page(self):
        """A registered user can view an organization's project page."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        title = page.click_on_project()
        assert title == "Organization #0 Test Project"

    def test_new_organization_view(self):
        """An organization without projects has a different view."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page(new=True)

        welcome = page.get_welcome_message()
        assert "You're ready to go".upper() in welcome

        title = page.click_add_new_project_button()
        assert title == "PROJECTS: Add new"

    def test_navigate_back_to_organization_list(self):
        """A user can click on the index-link
        and it takes them back to the organizations list."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationPage(self)
        page.go_to()
        page.go_to_organization_page()

        page.go_back_to_organization_list()
        page.get_org_list_title()
