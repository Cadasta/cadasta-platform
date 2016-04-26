from base import FunctionalTest
from pages.Member import MemberPage
from pages.Login import LoginPage

from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from core.tests.factories import PolicyFactory, RoleFactory
from organization.models import Organization
from tutelary.models import Policy

from selenium.webdriver.common.by import By

class MemberTest(FunctionalTest):
    def setUp(self):
        super().setUp()

        # users
        users = []
        users.append(UserFactory.create(
            username='testsuperuser', password='password')
        )
        users.append(UserFactory.create(
            username='testuser', email='testuser@example.com',
            first_name='Test', last_name='User',
            password='password')
        )

        PolicyFactory.set_directory('../cadasta/config/permissions')
        pols = {}
        # Default policy is installed automatically when first user is
        # created.
        pols['default'] = Policy.objects.get(name='default')
        for pol in ['superuser', 'org-admin', 'project-manager',
                    'data-collector', 'project-user']:
            pols[pol] = PolicyFactory.create(name=pol, file=pol + '.json')
        roles = {}
        roles['superuser'] = RoleFactory.create(
            name='superuser', policies=[pols['default'], pols['superuser']]
        )
        users[0].assign_policies(roles['superuser'])

        orgs = []
        orgs.append(OrganizationFactory.create(
            name="Organization #0", add_users=users)
        )

        projs = []
        projs.append(ProjectFactory.create(
            name='Organization #0 Test Project',
            project_slug='test-project',
            description="""This is a test project.  This is a test project.
            This is a test project.  This is a test project.  This is a test
            project.  This is a test project.  This is a test project.  This
            is a test project.  This is a test project.""",
            organization=orgs[0],
            country='KE',
            extent=('SRID=4326;'
                    'POLYGON ((-5.1031494140625000 8.1299292850467957, '
                    '-5.0482177734375000 7.6837733211111425, '
                    '-4.6746826171875000 7.8252894725496338, '
                    '-4.8641967773437491 8.2278005261522775, '
                    '-5.1031494140625000 8.1299292850467957))')
        ))

    def test_member_information_displays(self):
        """The member page displays with the correct user information."""

        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")

        page = MemberPage(self)
        page.go_to(org.slug)

        member_form = page.get_member_info()

        assert "Test User" in member_form.text
        assert "testuser" in member_form.text
        assert "testuser@example.com" in member_form.text
        assert "Last login:" in member_form.text

    def test_changing_member_roles(self):
        """The member page displays with the correct user information."""

        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")

        page = MemberPage(self)
        page.go_to(org.slug)

        options = page.get_role_options()

        assert options["member"].text == options["selected"].text
        options["admin"].click()
        submit = page.get_button("submit")
        self.click_through(submit, self.BY_ORG_MEMBERS)

        members = page.get_members_row('[2]')
        self.click_through(members, self.BY_MEMBER_PAGE)

        options = page.get_role_options()
        assert options["admin"].text == options["selected"].text

    # Can I remove the member?
    def test_removing_member(self):
        """The member page displays with the correct user information."""

        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")

        page = MemberPage(self)
        page.go_to(org.slug)

        remove = page.get_remove_button()
        self.click_through(remove, self.BY_MODAL_FADE)
        confirm = page.get_confirm_button()
        self.click_through(confirm, self.BY_ORG_MEMBERS)

        page_title = page.get_members_title()
        assert page_title == "Members".upper()

        members = page.get_members_row('').text
        assert "Test User" not in members

    # Can I change their permissions on a project?
    def test_changing_member_project_permissions(self):
        """The member page displays with the correct user information."""

        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")

        page = MemberPage(self)
        page.go_to(org.slug)

        options = page.get_permission_options()
        assert options['selected'].text == options['pb'].text
        options["pm"].click()
        submit = page.get_button("submit")
        self.click_through(submit, self.BY_ORG_MEMBERS)

        members = page.get_members_row('[2]')
        self.click_through(members, self.BY_MEMBER_PAGE)

        options = page.get_permission_options()
        assert options['selected'].text == options['pm'].text
