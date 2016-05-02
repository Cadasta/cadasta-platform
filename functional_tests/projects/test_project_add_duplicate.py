from base import FunctionalTest
from pages.Project import ProjectPage
from pages.ProjectAdd import ProjectAddPage
from pages.ProjectList import ProjectListPage
from pages.Login import LoginPage


class ProjectAddDuplicateTest(FunctionalTest):

    def setUp(self):
        super().setUp()

        # Define 1 OA
        self.test_data = {
            'orgadmin': {
                'username': 'orgadmin',
                'password': 'password1',
            },
        }
        self.test_data['users'] = (
            self.test_data['orgadmin'],
        )

        # Define 1 org the OA is an admin of
        self.test_data['orgs'] = [
            {
                'name': "UNESCO",
                'slug': 'unesco',
                'description': (
                    "United Nations Educational, Scientific, " +
                    "and Cultural Organization"
                ),
                'logo': (
                    'https://upload.wikimedia.org/wikipedia/commons/' +
                    'thumb/b/bc/UNESCO_logo.svg/320px-UNESCO_logo.svg.png'
                ),
                '_members': (0,),
                '_admins': (0,),
            },
        ]

        # Define 1 project that will be duplicated
        self.test_data['projects'] = [
            {
                'name': "Project Gutenberg",
                'slug': 'project-gutenberg',
                'description': "Public project of UNESCO.",
                'country': 'PH',
                'access': 'public',
                '_org': 0,
                '_managers': (0,),
            },
        ]

        self.load_test_data(self.test_data)

    def test_add_duplicate_project(self):
        """Verify that adding a project with the same name as an existing
        project will be successful. This specifically tests the unique
        project slug field constraint."""

        org = self.test_data['orgs'][0]
        project = {
            'name': "Project Gutenberg",
            'slug': 'project-gutenberg-1',
            'description': "",
            'country': '',
            'access': 'public',
            '_org_slug': org['slug'],
            '_org_name': org['name'],
            '_org_logo': org['logo'] if 'logo' in org else '',
        }

        # Log in as org admin
        LoginPage(self).login(
            self.test_data['orgadmin']['username'],
            self.test_data['orgadmin']['password'],
        )

        proj_add_page = ProjectAddPage(self)
        proj_add_page.go_to()

        proj_add_page.submit_geometry()
        proj_add_page.set_name(project['name'])
        proj_add_page.submit_details()
        proj_add_page.submit_permissions()

        # Check that we are now in the project page
        # and that displayed project details are correct
        proj_page = ProjectPage(self, project['_org_slug'], project['slug'])
        assert proj_page.is_on_page()
        proj_page.check_page_contents(project)

        old_project = self.test_data['projects'][0].copy()
        old_project['_org_slug'] = org['slug']
        old_project['_org_name'] = org['name']
        old_project['_org_logo'] = org['logo'] if 'logo' in org else ''

        # Go to project list and check that details are correct
        proj_list_page = ProjectListPage(self)
        proj_list_page.go_to_and_check_on_page()
        proj_list_page.check_project_list([old_project, project])

        self.logout()
