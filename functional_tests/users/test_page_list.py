import re

from datetime import datetime, timedelta, timezone
from django.utils import formats
from base import FunctionalTest
from fixtures import load_test_data
from pages.Users import UsersPage
from pages.Login import LoginPage
from core.tests.factories import PolicyFactory


class PageListTest(FunctionalTest):

    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()

        # Define 1 superuser and 9 other users
        users = []
        users.append({
            'username': 'superuser',
            'password': 'password3',
            'email': "superuser@example.com",
            'is_active': True,
            '_is_superuser': True,
        })
        for uid in range(1, 10):
            if uid < 5:
                last_login_val = (
                    datetime.now(tz=timezone.utc) -
                    timedelta(days=uid)
                )
            else:
                last_login_val = None
            users.append({
                'username': 'default' + str(uid),
                'password': 'password1',
                'email': "default" + str(uid) + "@example.com",
                'last_login': last_login_val,
                'is_active': (uid % 2 == 1),
            })
        self.test_data = {
            'users': users,
        }
        self.superuser = users[0]

        # Define 2 orgs and their members
        self.test_data['orgs'] = [
            {
                'name': "Organization One",
                '_members': (1, 2, 3, 4),
            },
            {
                'name': "Organization Two",
                '_members': (3, 4, 5, 6),
            },
        ]

        load_test_data(self.test_data)

    def test_list(self):
        """The index page should display the complete and correct user
        information."""

        # Get time now for superuser's last login time
        login_time = datetime.now(tz=timezone.utc)

        LoginPage(self).login(self.superuser['username'],
                              self.superuser['password'])

        users_page = UsersPage(self)
        users_page.go_to()

        users = self.test_data['users']
        assert users_page.get_num_users() == len(users)

        # Construct list of orgs each user is in
        # (Basically, invert the '_members' test data)
        for user in users:
            user['orgs'] = []
        for org in self.test_data['orgs']:
            for idx in org['_members']:
                users[idx]['orgs'].append(org)

        for user in users:

            username = user['username']

            # Check email is displayed correctly
            expected_email = user['email'] or '—'
            actual_email = users_page.get_user_email(username)
            assert actual_email == expected_email

            # Check organizations are displayed correctly
            actual_orgs = users_page.get_user_orgs(username)
            if len(user['orgs']) == 0:
                assert actual_orgs == '—'
            else:
                for org in user['orgs']:
                    assert org['name'] in actual_orgs
                    actual_orgs = actual_orgs.replace(org['name'], '')
                assert re.match('^[, ]*$', actual_orgs)

            # Check last login is displayed correctly
            if user == self.superuser:
                # Fuzzy checking for superuser
                try:
                    self.check_last_login(username, login_time)
                except AssertionError:
                    login_time = login_time + timedelta(minutes=1)
                    self.check_last_login(username, login_time)
            else:
                self.check_last_login(username, user['last_login'])

            # Check active status is displayed correctly
            assert (
                users_page.is_user_active(username) ==
                bool(user['is_active'])
            )

    def check_last_login(self, username, expected_time):
        actual = UsersPage(self).get_user_last_login(username)
        expected = (
            formats.date_format(expected_time, "DATETIME_FORMAT")
            if expected_time else '—'
        )
        assert actual == expected
