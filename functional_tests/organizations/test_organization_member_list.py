from base import FunctionalTest
from fixtures import load_test_data
from fixtures.common_test_data_2 import get_test_data
from pages.OrganizationMemberList import OrganizationMemberListPage
from pages.Organization import OrganizationPage
from pages.OrganizationMember import OrganizationMemberPage
from pages.Login import LoginPage

from accounts.tests.factories import UserFactory
from organization.models import OrganizationRole
from core.tests.factories import PolicyFactory


class OrganizationMemberListTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        test_objs = load_test_data(get_test_data())
        OrganizationRole.objects.create(
                organization=test_objs['organizations'][0],
                user=UserFactory.create(
                        username='admin_user',
                        password='password'),
                admin=True)
        UserFactory.create(
            username='hansolo',
            email='millenniumfalcon@example.com',
            full_name="Han Solo",
            password='password')

    def test_registered_user_view(self):
        """A registered admin user can view the member list."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberListPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()

        title = page.go_to_member_list_page()
        assert title == "Members".upper()

    def test_adding_members(self):
        """A registered admin user can add members to an organization."""

        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberListPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        page.go_to_member_list_page()

        page.click_on_add_button()
        page.try_cancel_and_close()

        input_box = page.click_on_input()
        error_list = page.click_submit_button(success=False)
        assert error_list == 'This field is required.'

        input_box = page.click_on_input()
        input_box.send_keys("darthvader")
        error_list = page.click_submit_button(success=False)
        error_message = 'User with username or email darthvader does not exist'
        assert error_list == error_message

        input_box = page.click_on_input()
        input_box.clear()
        input_box.send_keys("admin_user")
        error_list = page.click_submit_button(success=False)
        error_message = 'User is already a member of the organization.'
        assert error_list == error_message

        input_box = page.click_on_input()
        input_box.clear()
        input_box.send_keys("hansolo")
        member = page.click_submit_button()
        assert member == "MEMBER: Han Solo"

        OrganizationMemberPage(self).click_remove_member_and_confirm_buttons()

        page.click_on_add_button()
        input_box = page.click_on_input()
        input_box.send_keys("millenniumfalcon@example.com")
        member = page.click_submit_button()
        assert member == "MEMBER: Han Solo"

    def test_adding_members_to_archived_organization(self):
        LoginPage(self).login('admin_user', 'password')
        page = OrganizationMemberListPage(self)
        page.go_to()
        OrganizationPage(self).go_to_organization_page()
        OrganizationPage(self).get_archive_button()
        OrganizationPage(self).click_on_archive_and_confirm()

        title = page.go_to_member_list_page()
        assert title == "Members".upper()
        page.click_on_add_button(success=False)
