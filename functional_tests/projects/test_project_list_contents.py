from base import FunctionalTest
from pages.ProjectList import ProjectListPage
from pages.Login import LoginPage
from common_test_data.common_test_data_1 import get_test_data
from core.tests.factories import PolicyFactory

# from accounts.models import User


class ProjectListContentsTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        self.test_data = get_test_data()
        self.load_test_data(self.test_data)

    def check_project_list(self, user_type, parent_org_idxs):

        orgs = self.test_data['orgs']
        projects = self.test_data['projects']

        # Go to the project list page
        page = ProjectListPage(self)
        page.go_to_and_check_on_page()

        # Collect projects that are visible to the target user
        visible_projects = []
        for project in projects:
            if (
                user_type == 'superuser' or
                project['access'] == 'public' or (
                    user_type == 'affiliated' and
                    project['_org'] in parent_org_idxs
                )
            ):
                project_copy = project.copy()
                org = orgs[project['_org']]
                project_copy['_org_slug'] = org['slug']
                project_copy['_org_name'] = org['name']
                project_copy['_org_logo'] = (
                    org['logo'] if 'logo' in org else ''
                )
                visible_projects.append(project_copy)

        # Check that visible projects are present with correct details
        page.check_project_list(visible_projects)

    def generic_test_for_user(self, user_type):
        """Generic test method to verify that a user can see the
        visible projects and that project details are correct."""

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

            # Log in as the selected user, check the list, log out
            LoginPage(self).login(user['username'], user['password'])
            # u = User.objects.get(username=user['username'])
            # print(user['username'], '=>', u.assigned_policies())
            self.check_project_list(user_type, parent_org_idxs)
            self.logout()

    # FAILS: issue #188
    def test_nonloggedin_user(self):
        """Verify that a non-logged-in user can only see
        public projects and that project details are correct."""
        self.check_project_list('nonloggedin', [])

    def test_unaffiliated_user(self):
        """Verify that a user who is not a member of any org can
        only see public projects and that project details are correct."""
        self.generic_test_for_user('unaffiliated')

    def test_affiliated_user(self):
        """Verify that every affiliated non-superuser can see all projects
        of their organizations and the public projects of other organizations,
        and that project details are correct."""
        self.generic_test_for_user('affiliated')

    def test_superuser(self):
        """Verify that a superuser can see all projects,
        and that project details are correct."""
        self.generic_test_for_user('superuser')
