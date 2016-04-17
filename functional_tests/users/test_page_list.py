import re

from datetime import datetime, timedelta, timezone
from django.utils import formats
from base import FunctionalTest
from pages.Users import UsersPage
from pages.Login import LoginPage
from accounts.models import User
from accounts.tests.factories import UserFactory
from core.tests.factories import PolicyFactory, RoleFactory
from organization.tests.factories import OrganizationFactory
from organization.models import OrganizationRole


class PageListTest(FunctionalTest):

    def setUp(self):
        super().setUp()

        users = {}
        users['superuser'] = UserFactory.create(
            username='superuser',
            password='password2',
            email='superuser@cadasta.org',
            email_verified=True,
            last_login=datetime.now(tz=timezone.utc),
            is_active=True,
        )
        for uid in range(1, 10):
            if uid < 5:
                last_login_val = (
                    datetime.now(tz=timezone.utc) -
                    timedelta(days=uid)
                )
            else:
                last_login_val = None
            users["default" + str(uid)] = UserFactory.create(
                username="default" + str(uid),
                password='password1',
                email="default" + str(uid) + "@example.com",
                last_login=last_login_val,
                is_active=(uid % 2 == 1),
            )

        pols = {}
        PolicyFactory.set_directory('../cadasta/config/permissions')
        pols['default'] = PolicyFactory.create(
            name='default',   file='default.json'
        )
        pols['superuser'] = PolicyFactory.create(
            name='superuser', file='superuser.json'
        )

        roles = {}
        roles['superuser'] = RoleFactory.create(
            name='superuser',
            policies=[pols['default'], pols['superuser']],
        )

        users['superuser'].assign_policies(roles['superuser'])

        orgs = {}
        orgs['org1'] = OrganizationFactory.create(
            name='Organization One',
            slug='organization1',
            description="Description One",
            urls=['http://www.organization1.org'],
            logo='https://s3.amazonaws.com/cadasta-dev-tmp/logos/h4h.png',
            contacts=[{'email': 'info@organization1.org'}],
        )
        orgs['co2'] = OrganizationFactory.create(
            name='Company Two',
            slug='company2',
            description="Description Two",
            urls=['http://www.company2.org'],
            logo='https://s3.amazonaws.com/cadasta-dev-tmp/logos/cadasta.png',
            contacts=[{'email': 'company2.org'}]
        )

        OrganizationRole.objects.create(
            organization=orgs['org1'], user=users['default1']
        )
        OrganizationRole.objects.create(
            organization=orgs['org1'], user=users['default2']
        )
        OrganizationRole.objects.create(
            organization=orgs['org1'], user=users['default3']
        )
        OrganizationRole.objects.create(
            organization=orgs['org1'], user=users['default7']
        )
        OrganizationRole.objects.create(
            organization=orgs['co2'], user=users['default4']
        )
        OrganizationRole.objects.create(
            organization=orgs['co2'], user=users['default5']
        )
        OrganizationRole.objects.create(
            organization=orgs['co2'], user=users['default6']
        )
        OrganizationRole.objects.create(
            organization=orgs['co2'], user=users['default7']
        )

    def test_list(self):
        """The index page should display the complete and correct user
        information."""

        LoginPage(self).login('superuser', 'password2')
        UsersPage(self).go_to()

        tableBody = self.browser.find_element_by_xpath(
            "//table[@id='DataTables_Table_0']/tbody"
        )
        rows = tableBody.find_elements_by_xpath("tr")
        users = User.objects.all()
        assert len(rows) == len(users)

        for user in users:
            # User's row must exist
            row = tableBody.find_element_by_xpath(
                "tr[./td[1][text()='{}' and not(*[2])]]".format(user.username)
            )

            formatted_email = user.email or '—'
            row.find_element_by_xpath(
                "td[2][text()='{}' and not(*[2])]".format(formatted_email)
            )

            if user.organizations.count() == 0:
                row.find_element_by_xpath(
                    "td[3][text()='—' and not(*[2])]"
                )
            else:
                cell_text = row.find_element_by_xpath("td[3][not(*[2])]").text
                for org in user.organizations.all():
                    assert org.name in cell_text
                    cell_text = cell_text.replace(org.name, '')
                assert re.match('^[, ]*$', cell_text)

            formatted_last_login = (
                formats.date_format(user.last_login, "DATETIME_FORMAT")
                if user.last_login else '—'
            )
            row.find_element_by_xpath(
                "td[4][text()='{}' and not(*[2])]".format(formatted_last_login)
            )

            action_slug = 'deactivate' if user.is_active else 'activate'
            row.find_element_by_xpath(
                "td[5][form[@action='/users/{}/{}/']]".format(user.username,
                                                              action_slug)
            )
