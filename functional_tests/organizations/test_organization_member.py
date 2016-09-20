from base import FunctionalTest
from fixtures import load_test_data
from fixtures.common_test_data_2 import get_test_data
from pages.OrganizationMember import OrganizationMemberPage
from pages.Organization import OrganizationPage
from pages.OrganizationList import OrganizationListPage
from pages.OrganizationMemberList import OrganizationMemberListPage
from pages.Login import LoginPage

from accounts.tests.factories import UserFactory
from organization.models import OrganizationRole
from core.tests.factories import PolicyFactory


class OrganizationMemberTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        test_objs = load_test_data(get_test_data())
        OrganizationRole.objects.create(
                organization=test_objs['organizations'][0],
                user=UserFactory.create(
                        username='admin_user',
                        full_name='Admin User',
                        password='password'),
                admin=True)

    def test_that_an_individual_members_information_displays(self):
        """The organization's individual member page
        displays with the correct user information."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationMemberListPage(self).go_to_member_list_page()

        testuser_title = page.go_to_testuser_member_page()
        assert "MEMBER: Test User" == testuser_title

        member_form = page.get_displayed_member_info()

        assert "Test User" in member_form.text
        assert "testuser" in member_form.text
        assert "testuser@example.com" in member_form.text
        assert "Last login:" in member_form.text

    def test_changing_a_members_organizational_role(self):
        """An admin member can change a member's role in the organization."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationMemberListPage(self).go_to_member_list_page()
        page.go_to_testuser_member_page()

        roles = page.get_role_options()
        assert roles["member"].text == roles["selected"].text

        roles["admin"].click()
        page.click_submit_button()
        page.go_to_testuser_member_page()

        roles = page.get_role_options()
        assert roles["admin"].text == roles["selected"].text

    def test_changing_an_admins_organizational_role(self):
        """An admin member can change a member's role in the organization."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationMemberListPage(self).go_to_member_list_page()
        page.go_to_admin_member_page()

        roles = page.get_role_options()
        assert roles["admin"].text == roles["selected"].text

        roles["member"].click()
        page.click_submit_button()
        self.get_screenshot()
        # get error message
        # assert you stayed on the same page.
        roles = page.get_role_options()
        errors = page.get_org_role_error()
        assert errors.text == ("Organization administrators cannot change" +
                               " their own role in the organization.")

    def test_removing_a_member_from_an_organization(self):
        """An admin member can remove a member from an organization."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationMemberListPage(self).go_to_member_list_page()
        page.go_to_testuser_member_page()

        page.try_cancel_and_close()
        assert page.get_member_title() == "MEMBER: Test User"

        page.click_remove_member_and_confirm_buttons()

        members = page.get_table_row().text
        assert "Test User" not in members

    def test_removing_an_admin_member_from_an_organization(self):
        """An admin member can remove a member from an organization."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationMemberListPage(self).go_to_member_list_page()
        page.go_to_admin_member_page()

        assert page.get_member_title() == "MEMBER: Admin User"

        page.click_disabled_remove_button()
        assert page.get_member_title() == "MEMBER: Admin User"

    def test_changing_member_project_permissions(self):
        """An admin user can change a member's permissions
        on individual projects."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationMemberListPage(self).go_to_member_list_page()
        page.go_to_testuser_member_page()

        options = page.get_permission_options()
        assert options['selected'].text == options['pb'].text
        options["pm"].click()

        page.click_submit_button()
        page.go_to_testuser_member_page()

        options = page.get_permission_options()
        assert options['selected'].text == options['pm'].text

    def test_admin_creation_when_adding_organization(self):
        """A user that can create a new organization and
        is automatically made an admin."""

        LoginPage(self).login('testuser', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()

        OrganizationListPage(self).click_add_button()
        fields = OrganizationListPage(self).get_fields()
        fields['name'].send_keys('Organization #2')
        fields['description'].send_keys('This is a test organization')
        OrganizationListPage(self).click_submit_button()

        OrganizationMemberListPage(self).go_to_member_list_page()
        page.go_to_testuser_member_page()

        roles = page.get_role_options()
        assert roles['selected'].text == "Administrator"

    def test_editing_member_in_archived_organization(self):
        """A user that can create a new organization and
        is automatically made an admin."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationPage(self).get_archive_button()
        OrganizationPage(self).click_on_archive_and_confirm()
        OrganizationMemberListPage(self).go_to_member_list_page()

        testuser_title = page.go_to_testuser_member_page(success=False)
        assert "MEMBER: Test User" != testuser_title
