from allauth.account.models import EmailAddress
from core.tests.utils.cases import UserTestCase
from django.contrib.auth.models import Group
from django.test import TestCase
from organization.models import ProjectRole
from organization.tests.factories import ProjectFactory

from ..backends import AuthenticationBackend
from core.backends import RoleAuthorizationBackend

from .factories import UserFactory


class AuthBackendTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            username='kindofblue',
            email='miles@davis.co',
            password='PlayTh3Trumpet!'
        )
        self.backend = AuthenticationBackend()

    def test_login_with_email(self):
        credentials = {'email': 'miles@davis.co',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend._authenticate_by_email(**credentials) == self.user

    def test_login_with_unapproved_email(self):
        EmailAddress.objects.create(
            user=self.user,
            email='miles2@davis.co',
            verified=False,
            primary=True
        )
        credentials = {'email': 'miles2@davis.co',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend._authenticate_by_email(**credentials) is None

    def test_auth_in_username_field(self):
        credentials = {'username': 'miles@davis.co',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend._authenticate_by_email(**credentials) == self.user


class RoleAuthorizationBackendTest(UserTestCase, TestCase):

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.user = UserFactory.create(
            username='kindofblue',
            email='miles@davis.co',
            password='PlayTh3Trumpet!'
        )
        self.backend = RoleAuthorizationBackend()

    def test_has_perm_with_missing_role(self):
        assert self.backend.has_perm(self.user, 'org.create') is False

    def test_has_perm(self):
        group = Group.objects.get(name='OrgAdmin')
        role = ProjectRole.objects.create(
            user=self.user, project=self.project, group=group)
        assert len(role.permissions) == 26
        assert self.backend.has_perm(self.user, 'org.create', obj=role)
        assert self.backend.has_perm(
            self.user, 'project.create', obj=role) is True
