from selenium.webdriver.common.by import By

import geography.load

from base import FunctionalTest
from fixtures import load_test_data
from pages.Project import ProjectPage
from pages.ProjectAdd import ProjectAddPage
from pages.ProjectList import ProjectListPage
from pages.Login import LoginPage
from pages.Dashboard import DashboardPage
from core.tests.factories import PolicyFactory


class ProjectAddTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()

        # Load world boundary data
        geography.load.run(verbose=False)

        # Define 1 SU, 1 OA, 1 org member, and 1 unaffiliated user
        self.test_data = {
            'superuser': {
                'username': 'superuser',
                'password': 'password2',
                '_is_superuser': True,
            },
            'orgadmin': {
                'username': 'orgadmin',
                'password': 'password1',
            },
            'orgmember': {
                'username': 'orgmember',
                'password': 'password3',
            },
            'unaffuser': {
                'username': 'plainuser',
                'password': 'password4',
            },
        }
        self.test_data['users'] = [
            {
                'username': 'superuser',
                'password': 'password2',
                '_is_superuser': True,
            },
            {
                'username': 'orgadmin',
                'password': 'password1',
            },
            {
                'username': 'orgmember',
                'password': 'password3',
            },
            {
                'username': 'plainuser',
                'password': 'password4',
            }
        ]
        (self.superuser, self.orgadmin,
         self.orgmember, self.unaffuser) = self.test_data['users']

        # Define 2 orgs the OA is an admin of and 1 other org
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
                '_members': (1, 2),
                '_admins': (1,),
            },
            {
                'name': "UNICEF",
                'slug': 'unicef',
                'description': "United Nations Children's Emergency Fund",
                '_members': (1,),
                '_admins': (1,),
            },
            {
                'name': "UNOCHA",
                'slug': 'unocha',
                'description': (
                    "United Nations " +
                    "Office for the Coordination of Humanitarian Affairs"
                ),
                '_members': [],
                '_admins': [],
            },
        ]

        # Search terms to specify a country
        self.test_data['countries'] = {
            'FR': "Paris, France",
            'RU': "Moscow, Russia",
            'AU': "Canberra, Australia",
            'DE': "Berlin, Germany",
        }

        self.test_data['project_slug'] = 'post-sokovia-land-tenure-project'
        self.test_data['project_name'] = "Post-Sokovia Land Tenure Project"
        self.test_data['project_description'] = (
            "This project aims to document land tenure in what is left of " +
            "Sokovia, which was destroyed during a conflict involving the " +
            "Avengers, a rogue vigilante group."
        )
        self.test_data['project_url'] = 'http://sokovia-accords.un.org/'

        load_test_data(self.test_data)

    def test_nonloggedin_user(self):
        """A non-logged-in user cannot access the add project page,
        but will be directed to it once logged in as a superuser."""

        self.browser.get(ProjectAddPage(self).url)
        assert LoginPage(self).is_on_page()
        assert self.get_url_query() == 'next=' + ProjectAddPage.path

        LoginPage(self).login(
            self.superuser['username'], self.superuser['password'],
            wait=(By.ID, 'project-wizard')
        )
        assert ProjectAddPage(self).is_on_page()

    def xtest_unaffiliated_user(self):
        # TODO: Expected behavior is not yet implemented
        # Expected behavior is that user is denied access outright
        pass

    def generic_test_orgadmin(self, access):

        assert access in ('public', 'private')

        # Log in as org admin
        LoginPage(self).login(self.orgadmin['username'],
                              self.orgadmin['password'])

        # Declare working project data for verification
        project = {}

        proj_add_page = ProjectAddPage(self)
        proj_add_page.go_to()
        assert proj_add_page.is_on_page()
        assert proj_add_page.is_on_subpage('geometry')

        # Select country and submit geometry
        project['country'] = 'AU' if access == 'public' else 'BR'
        proj_add_page.set_geometry(project['country'])
        proj_add_page.submit_geometry()

        # Check that details are all blank/default
        project['org'] = 'unesco'
        project['name'] = ""
        project['access'] = 'public'
        project['description'] = ""
        project['url'] = ''
        proj_add_page.check_details(project)

        # TODO: Check that only valid orgs are provided
        # TODO: Vary org selection

        # Check that an error occurs when no project name was set
        # Also toggle access and set description
        project['access'] = 'private'
        project['description'] = self.test_data['project_description']
        proj_add_page.set_access(project['access'])
        proj_add_page.set_description(project['description'])
        proj_add_page.try_submit_details()
        proj_add_page.check_missing_name_error()
        proj_add_page.check_details(project)

        # Check that an error occurs when the project name is only whitespace
        # Also toggle access and set URL
        project['name'] = "     "
        project['access'] = 'public'
        project['url'] = self.test_data['project_url']
        proj_add_page.set_name(project['name'])
        proj_add_page.set_access(project['access'])
        proj_add_page.set_proj_url(project['url'])
        proj_add_page.try_submit_details()
        proj_add_page.check_missing_name_error()
        proj_add_page.check_details(project)

        # Set project name, final access, and invalid URL
        # Check that the page is not submitted due to the invalid URL
        # (This is an HTML5 feature)
        project['name'] = self.test_data['project_name']
        project['access'] = access
        project['url'] = "DEADBEEF"
        proj_add_page.set_name(project['name'])
        proj_add_page.set_access(project['access'])
        proj_add_page.set_proj_url(project['url'])
        proj_add_page.click_submit_details()
        proj_add_page.check_details(project)

        # Correct the URL, press "Previous" then "Next" and ensure
        # that details settings are preserved.
        project['url'] = self.test_data['project_url']
        proj_add_page.set_proj_url(project['url'])
        proj_add_page.click_previous_details()
        proj_add_page.submit_geometry()
        proj_add_page.check_details(project)

        # Finally submit details
        proj_add_page.submit_details()

        # Set permissions
        # TODO: Vary permissions and check permissions after
        proj_add_page.submit_permissions()

        # Set project slug and org details
        project['slug'] = self.test_data['project_slug']
        orgs = self.test_data['orgs']
        project['_org_slug'] = orgs[0]['slug']
        project['_org_name'] = orgs[0]['name']
        project['_org_logo'] = (
            orgs[0]['logo'] if 'logo' in orgs[0] else ''
        )

        # Check that we are now in the project page
        # and that displayed project details are correct
        proj_page = ProjectPage(self, project['_org_slug'], project['slug'])
        assert proj_page.is_on_page()
        proj_page.check_page_contents(project)

        # Go to project list and check that details are correct
        proj_list_page = ProjectListPage(self)
        proj_list_page.go_to_and_check_on_page()
        proj_list_page.check_project_list([project])

        self.logout()

        # Check new project as an org member
        LoginPage(self).login(self.orgmember['username'],
                              self.orgmember['password'])
        proj_page.go_to()
        assert proj_page.is_on_page()
        proj_page.check_page_contents(project)
        proj_list_page = ProjectListPage(self)
        proj_list_page.go_to_and_check_on_page()
        proj_list_page.check_project_list([project])
        self.logout()

        # Check new project as an unaffiliated user
        LoginPage(self).login(self.unaffuser['username'],
                              self.unaffuser['password'])
        proj_page.go_to()
        if access == 'public':
            assert proj_page.is_on_page()
            proj_page.check_page_contents(project)
        else:
            assert DashboardPage(self).is_on_page()
            self.assert_has_message('alert', "have permission")
        proj_list_page = ProjectListPage(self)
        proj_list_page.go_to_and_check_on_page()
        if access == 'public':
            proj_list_page.check_project_list([project])
        else:
            assert proj_list_page.is_list_empty()
        self.logout()

    def test_orgadmin_public_project(self):
        self.generic_test_orgadmin('public')

    def test_orgadmin_private_project(self):
        self.generic_test_orgadmin('private')
