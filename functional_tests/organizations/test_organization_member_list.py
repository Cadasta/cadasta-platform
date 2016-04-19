from base import FunctionalTest
from pages.OrganizationMemberList import OrganizationMemberListPage
from pages.Organization import OrganizationPage
from pages.OrganizationMember import OrganizationMemberPage
from pages.Login import LoginPage

from accounts.tests.factories import UserFactory
from organization.models import OrganizationRole


class OrganizationMemberListTest(FunctionalTest):
    def setUp(self):
        super().setUp()

        orgs = self.add_all_test_data()
        OrganizationRole.objects.create(
                organization=orgs[0],
                user=UserFactory.create(
                        username='admin_user',
                        password='password'),
                admin=True)
        UserFactory.create(
            username='hansolo',
            email='millenniumfalcon@example.com',
            first_name="Han",
            last_name="Solo",
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
        input_box.send_keys("hansolo")
        member = page.click_submit_button()
        assert member == "MEMBER: Han Solo"

        OrganizationMemberPage(self).click_remove_member_and_confirm_buttons()

        page.click_on_add_button()
        input_box = page.click_on_input()
        input_box.send_keys("millenniumfalcon@example.com")
        member = page.click_submit_button()
        assert member == "MEMBER: Han Solo"
