from base import FunctionalTest
from fixtures import load_test_data
from pages.Project import ProjectPage
from pages.ProjectAdd import ProjectAddPage
from pages.ProjectList import ProjectListPage
from pages.Login import LoginPage
from core.tests.factories import PolicyFactory


class ProjectAddDuplicateTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()

        # Define 1 OA
        self.test_data = {
            'users': [
                {
                    'username': 'orgadmin',
                    'password': 'password1',
                }
            ]
        }
        self.orgadmin = self.test_data['users'][0]

        # Define 2 orgs the OA is an admin of
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
            {
                'name': "UNICEF",
                'slug': 'unicef',
                'description': (
                    "United Nations Children's Emergency Fund"
                ),
                '_members': (),
                '_admins': (),
            },
        ]

        # Define 2 projects that will be duplicated in separate orgs
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
            {
                'name': "Wikipedia",
                'slug': 'wikipedia',
                'description': "Public project of UNICEF.",
                'country': 'AU',
                'access': 'public',
                '_org': 1,
                '_managers': (),
            },
        ]

        load_test_data(self.test_data)

    def generic_test_add_duplicate_project(self, from_same_org=True):

        org = self.test_data['orgs'][0]
        project = {
            'description': "",
            'country': '',
            'access': 'public',
            '_org_slug': org['slug'],
            '_org_name': org['name'],
            '_org_logo': org['logo'] if 'logo' in org else '',
        }
        duplicated_proj_idx = 0 if from_same_org else 1
        duplicated_proj = self.test_data['projects'][duplicated_proj_idx]
        project['name'] = duplicated_proj['name']
        project['slug'] = duplicated_proj['slug'] + '-1'

        # Log in as org admin
        LoginPage(self).login(self.orgadmin['username'],
                              self.orgadmin['password'])

        # Go to the add project wizard and
        # proceed to step 2 and input the project name
        proj_add_page = ProjectAddPage(self)
        proj_add_page.go_to()
        proj_add_page.submit_geometry()
        proj_add_page.set_name(project['name'])

        if from_same_org:
            # If project name is duplicate from the same org, expect that
            # submitting step 2 will result in an error
            proj_add_page.try_submit_details()
            proj_add_page.check_duplicate_name_error()

            # Make the name unique
            project['name'] = project['name'] + " 1"
            proj_add_page.set_name(project['name'])

        # successfully complete the add project wizard
        proj_add_page.submit_details()
        proj_add_page.submit_permissions()

        # Check that we are now in the new project page
        # and that the displayed project details are correct
        proj_page = ProjectPage(self, project['_org_slug'], project['slug'])
        assert proj_page.is_on_page()
        proj_page.check_page_contents(project)

        # Construct final list of projects that should be in the DB
        expected_projs = []
        for proj in self.test_data['projects']:
            proj_copy = proj.copy()
            proj_org = self.test_data['orgs'][proj['_org']]
            proj_copy['_org_slug'] = proj_org['slug']
            proj_copy['_org_name'] = proj_org['name']
            proj_copy['_org_logo'] = (
                proj_org['logo'] if 'logo' in proj_org else '')
            expected_projs.append(proj_copy)
        expected_projs.append(project)

        # Go to project list and check that details are correct
        proj_list_page = ProjectListPage(self)
        proj_list_page.go_to_and_check_on_page()
        proj_list_page.check_project_list(expected_projs)

        self.logout()

    def test_add_duplicate_project(self):
        """Verify that adding a project with the same name as an existing
        project will not be successful until corrected."""
        self.generic_test_add_duplicate_project(from_same_org=True)

    def test_add_duplicate_project_in_another_org(self):
        """Verify that adding a project with the same name as an existing
        project in another org will be successful. This specifically
        tests the unique project slug field constraint."""
        self.generic_test_add_duplicate_project(from_same_org=False)
