from base import FunctionalTest
from pages.Organizations import OrganizationsPage
from pages.Login import LoginPage
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from core.tests.factories import PolicyFactory, RoleFactory
from selenium.webdriver.common.by import By


class OrganizationsTest(FunctionalTest):
    def setUp(self):
        super().setUp()

        users = []
        users.append(UserFactory.create(
            username='testsuperuser', password='password')
        )
        users.append(UserFactory.create(
            username='testuser', password='password')
        )

        PolicyFactory.set_directory('../cadasta/config/permissions')
        pols = {}
        for pol in ['default', 'superuser', 'org-admin', 'project-manager',
                    'data-collector', 'project-user']:
            pols[pol] = PolicyFactory.create(name=pol, file=pol + '.json')
        roles = {}
        roles['superuser'] = RoleFactory.create(
            name='superuser', policies=[pols['default'], pols['superuser']]
        )
        users[0].assign_policies(roles['superuser'])

        orgs = []
        orgs.append(OrganizationFactory.create(
            name="Organization #0", description='This is a test.',
            add_users=users)
        )
        orgs.append(OrganizationFactory.create(
            name="Organization #1", description='This is a test.')
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

    def test_organizations_view_without_permission(self):
        """ Users without permission cannot view organizations """

        LoginPage(self).login('testuser', 'password')

        page = OrganizationsPage(self)
        page.go_to()

        empty_table = page.get_empty_table()
        assert empty_table.text == 'No data available in table'

    def test_organizations_view_with_permission(self):
        """A registered superuser user can view organizations"""

        LoginPage(self).login('testsuperuser', 'password')

        page = OrganizationsPage(self)
        page.go_to()

        organization_title = page.get_organization_titles()
        assert organization_title.text == 'Organization #0'

    def test_sorting_organization_view(self):
        """A registered superuser user can sort the organization list
        by id, name, and number of projects."""

        LoginPage(self).login('testsuperuser', 'password')

        page = OrganizationsPage(self)
        page.go_to()

        sorters = []
        sorters.append(page.get_id_sorter())
        sorters.append(page.get_name_sorter())
        sorters.append(page.get_project_sorter())

        # by id?

        # by organization name
        self.click_through(sorters[1], (By.CLASS_NAME, 'sorting_asc'))
        organization_title = page.get_organization_titles()
        assert organization_title.text == 'Organization #0'

        self.click_through(sorters[1], (By.CLASS_NAME, 'sorting_desc'))
        organization_title = page.get_organization_titles()
        assert organization_title.text == 'Organization #1'

        # by number of projects
        self.click_through(sorters[2], (By.CLASS_NAME, 'sorting_asc'))
        organization_title = page.get_organization_titles()
        assert organization_title.text == 'Organization #1'

        self.click_through(sorters[2], (By.CLASS_NAME, 'sorting_desc'))
        organization_title = page.get_organization_titles()
        assert organization_title.text == 'Organization #0'

    def test_searching_for_organizations(self):
        """A registered superuser user can search for organization by name."""

        LoginPage(self).login('testsuperuser', 'password')

        page = OrganizationsPage(self)
        page.go_to()

        search = page.get_search_box()
        search.send_keys("#1")

        organization_title = page.get_organization_titles()
        assert organization_title.text == 'Organization #1'

    def test_adding_an_organization(self):
        """A registered superuser can add an organization."""

        LoginPage(self).login('testsuperuser', 'password')

        page = OrganizationsPage(self)
        page.go_to()

        add_button = page.get_add_button()
        self.click_through(add_button, self.BY_MODAL)

        # error message should appear if there's no name.
        fields = page.get_fields()
        page.try_submit(err=['name'], ok=['description', 'urls'])

        # getting an error message for urls?
        fields = page.get_fields()
        fields['name'].send_keys('Organization #2')
        fields['description'].send_keys('This is a test organization')
        fields['urls'].send_keys('test.com')
        page.try_submit(err=['urls'], ok=['name', 'description', 'urls'])

        # clear urls field and submit.
        fields = page.get_fields()
        fields['urls'].clear()
        self.click_through(fields['add'], self.BY_ORG_DASH)
        organization_name = page.get_organization_name_from_dashboard()

        assert organization_name.text == 'ORGANIZATION #2'

    def test_cancelling_adding_an_organization(self):
        """A superuser can cancel adding an organization
        and it clears the fields"""
        LoginPage(self).login('testsuperuser', 'password')

        page = OrganizationsPage(self)
        page.go_to()

        add_button = page.get_add_button()
        self.click_through(add_button, self.BY_MODAL)

        close_buttons = ['cancel', 'close']
        for button in close_buttons:
            fields = page.get_fields()
            fields['name'].send_keys("Organization #3")
            fields['description'].send_keys("This should go away.")
            fields['urls'].send_keys("notstaying.com")

            cancel = page.get_close((button))
            self.click_through_close(cancel, (By.CLASS_NAME, 'modal-backdrop'))

            add_button = page.get_add_button()
            self.click_through(add_button, self.BY_MODAL)

            fields = page.get_fields()
            assert fields["name"].text == ""
            assert fields["description"].text == ""
            assert fields["urls"].text == ""
