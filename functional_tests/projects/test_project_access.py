from base import FunctionalTest
from fixtures import load_test_data
from pages.Project import ProjectPage
from pages.Login import LoginPage
from pages.Dashboard import DashboardPage
from fixtures.common_test_data_1 import get_test_data
from tutelary.models import assign_user_policies, Policy
from core.tests.factories import PolicyFactory


class ProjectAccessTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        self.test_data = get_test_data()
        load_test_data(self.test_data)

    def check_project_pages(self, user_type, parent_org_idxs):

        orgs = self.test_data['orgs']
        projects = self.test_data['projects']

        # Note which projects are visible to the target user
        # and append org attributes as well for each project
        for project in projects:

            org_idx = project['_org']
            org = orgs[org_idx]
            project_copy = project.copy()
            project_copy['_org_slug'] = org['slug']
            project_copy['_org_name'] = org['name']
            project_copy['_org_logo'] = (
                org['logo'] if 'logo' in org else ''
            )
            is_visible = (
                True if (
                    user_type == 'superuser' or
                    project['access'] == 'public' or
                    (user_type == 'affiliated' and org_idx in parent_org_idxs)
                ) else False
            )

            project_page = ProjectPage(self, org['slug'], project['slug'])
            project_page.go_to()

            if is_visible and project['archived'] is False:
                assert project_page.is_on_page()
                project_page.check_page_contents(project_copy)
            elif project['archived'] is False:
                assert DashboardPage(self).is_on_page()
                self.assert_has_message('alert', "have permission")

    def generic_test_for_user(self, user_type):
        """Generic test method to verify that a user can see the pages
        of visible projects and that project details are correct."""

        users = self.test_data['users']
        orgs = self.test_data['orgs']

        # Test each user
        for uidx in range(len(users)):

            user = users[uidx]
            parent_org_idxs = []

            # Skip if a user is not the target type
            is_superuser = '_is_superuser' in user and user['_is_superuser']
            if (
                (user_type == 'superuser' and not is_superuser) or
                (user_type != 'superuser' and is_superuser)
            ):
                continue
            if user_type == 'affiliated':
                parent_org_idxs = []
                for org_idx in range(len(orgs)):
                    if uidx in orgs[org_idx]['_members']:
                        parent_org_idxs.append(org_idx)
                        break
                if not len(parent_org_idxs):
                    continue
            elif user_type == 'unaffiliated':
                is_ok = True
                for org in orgs:
                    if uidx in org['_members']:
                        is_ok = False
                        break
                if not is_ok:
                    continue

            # Log in as the selected user, check the project pages, log out
            LoginPage(self).login(user['username'], user['password'])
            self.check_project_pages(user_type, parent_org_idxs)
            self.logout()

    # FAILS: issue #188
    def test_nonloggedin_user(self):
        """Verify that a non-logged-in user can only see
        pages of public projects and that project details are correct."""
        assign_user_policies(None, Policy.objects.get(name='default'))
        self.check_project_pages('nonloggedin', [])

    def test_unaffiliated_user(self):
        """Verify that a user who is not a member of any org can only see
        pages of public projects and that project details are correct."""
        self.generic_test_for_user('unaffiliated')

    def test_affiliated_user(self):
        """Verify that every affiliated non-superuser can see the pages of
        projects of their organizations and the pages of public projects of
        other organizations, and that project details are correct."""
        self.generic_test_for_user('affiliated')

    def test_superuser(self):
        """Verify that a superuser can see the pages of all projects,
        and that project details are correct."""
        self.generic_test_for_user('superuser')
