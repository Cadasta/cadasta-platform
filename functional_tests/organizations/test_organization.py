from base import FunctionalTest
from pages.Organization import OrganizationPage
from pages.Login import LoginPage

from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from core.tests.factories import PolicyFactory, RoleFactory
from organization.models import Organization
from selenium.webdriver.common.by import By
from tutelary.models import Policy


class OrganizationTest(FunctionalTest):
    def setUp(self):
        super().setUp()

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
        roles['superuser'] = RoleFactory.create(name='superuser',
                                                policies=[pols['default'],
                                                          pols['superuser']])
        users[0].assign_policies(roles['superuser'])

        orgs = []
        orgs.append(OrganizationFactory.create(
            name="Organization #0", description="This is a test.",
            add_users=users)
        )
        orgs.append(OrganizationFactory.create(
            name="New Organization", description="I don't have projects!",
            add_users=users)
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

    def test_organization_view(self):
        """A registered user can view an organization's dashboard.
           Org description and users are displayed."""
        LoginPage(self).login('testsuperuser', 'password')

        org = Organization.objects.get(name="Organization #0")

        page = OrganizationPage(self)
        page.go_to(org.slug)

        # Is there a description?
        info = page.get_org_description_and_members()
        assert "This is a test." in info.text
        # Are there users?
        assert "Test User" in info.text
        assert "Username: testuser" in info.text

    def test_edit_organization(self):
        """A registered user can edit an organization's information."""
        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")
        page = OrganizationPage(self)
        page.go_to(org.slug)

        page.get_edit_button()
        fields = page.get_fields()

        assert fields["name"].get_attribute("value") == "Organization #0"
        assert fields["description"].text == "This is a test."
        assert fields["urls"].text == ""

        fields["name"].clear()
        fields["name"].send_keys("Modified organization name")
        submit = page.get_submit()
        self.click_through_close(submit, (By.CLASS_NAME, 'modal-backdrop'))

        name = page.get_organization_logo_alt_text()
        assert "Modified organization name" in name

    def test_archiving_organization(self):
        """A registered user can archive/unarchive an organization."""
        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")
        page = OrganizationPage(self)
        page.go_to(org.slug)

        archive = page.get_archive_button()
        assert archive.text == "Archive organization"

        self.click_through(archive, self.BY_MODAL_FADE)
        final = page.get_archive_final()
        self.click_through_close(final, self.BY_MODAL_FADE)
        archive = page.get_archive_button()
        assert archive.text == "Unarchive organization"

        self.click_through(archive, self.BY_MODAL_FADE)
        final = page.get_unarchive_final()
        self.click_through_close(final, self.BY_MODAL_FADE)
        archive = page.get_archive_button()
        assert archive.text == "Archive organization"

    def test_getting_to_the_user_list(self):
        """A registered user can search for an organization's project."""
        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")
        page = OrganizationPage(self)
        page.go_to(org.slug)

        users_btn = page.get_users_page()
        self.click_through(users_btn, self.BY_ORG_MEMBERS)

    def test_navigating_to_project_page(self):
        """A registered user can edit an organization's information."""
        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="Organization #0")
        page = OrganizationPage(self)
        page.go_to(org.slug)

        project = page.get_project()
        self.click_through(project, (By.CLASS_NAME, "main-map"))
        title = page.get_project_title()
        assert title == "Organization #0 Test Project"

    def test_new_organization_view(self):
        """An organization without projects has a different view."""
        LoginPage(self).login('testsuperuser', 'password')
        org = Organization.objects.get(name="New Organization")
        page = OrganizationPage(self)
        page.go_to(org.slug)
        # Is there a welcome message?
        welcome = page.get_welcome_message()
        assert "You're ready to go".upper() in welcome.text

        # Can I add a new project?
        new_proj = page.get_new_project()
        self.click_through(new_proj, self.BY_NEW_PROJ)
        self.screenshot()

        # Can I add new members? (currently not working)
        page = OrganizationPage(self)
        page.go_to(org.slug)
        # add_member = page.get_add_members()
        # self.fail("Add test once add members button is up.")
        # self.click_through(add_members, self.BY_ADD_MEMBERS)

    # Can I search for a project
