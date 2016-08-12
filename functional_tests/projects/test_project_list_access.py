from base import FunctionalTest
from fixtures import load_test_data
from pages.ProjectList import ProjectListPage
from pages.Login import LoginPage
from core.tests.factories import PolicyFactory


class ProjectListAccessTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()

        # Define 1 superuser and 9 other users
        users = []
        users.append({
            'username': 'superuser',
            'password': 'password3',
            '_is_superuser': True,
        })
        for uid in range(1, 10):
            users.append({
                'username': 'default' + str(uid),
                'password': 'password1',
            })
        self.test_data = { 'users': users }
        self.superuser = users[0]

        # Define 2 orgs and their members
        self.test_data['orgs'] = [
            {
                'name': "UNESCO",
                'description': (
                    "United Nations Educational, Scientific, " +
                    "and Cultural Organization"
                ),
                '_members': (1, 2, 5, 6),
                '_admins': (1,),
            },
            {
                'name': "UNICEF",
                'description': "United Nations Children's Emergency Fund",
                '_members': (3, 4, 5, 6),
                '_admins': (3,),
            },
        ]

        load_test_data(self.test_data)

    def test_nonloggedin_user(self):
        """Verify that a non-logged-in user can access
        the project list page."""

        ProjectListPage(self).go_to_and_check_on_page()

    def test_nonsuperuser(self):
        """Verify that a non-superuser can access the project list page."""

        uid = 5
        LoginPage(self).login(self.test_data['users'][uid]['username'],
                              self.test_data['users'][uid]['password'])
        ProjectListPage(self).go_to_and_check_on_page()

    def test_superuser(self):
        """Verify that a superuser can access the project list page."""

        LoginPage(self).login(self.superuser['username'],
                              self.superuser['password'])
        ProjectListPage(self).go_to_and_check_on_page()
