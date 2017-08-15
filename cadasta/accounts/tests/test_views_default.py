import datetime
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase
from django.core import mail
from skivvy import ViewTestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase

from allauth.account.models import EmailConfirmation, EmailAddress
from allauth.account.forms import ChangePasswordForm

from ..views import default
from ..forms import ProfileForm
from organization.models import OrganizationRole, ProjectRole
from organization.tests.factories import ProjectFactory, OrganizationFactory


class ProfileTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountProfile
    template = 'accounts/profile.html'

    def setup_template_context(self):
        return {
            'form': ProfileForm(instance=self.user),
            'emails_to_verify': False
        }

    def test_get_profile(self):
        self.user = UserFactory.create()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_profile_with_unverified_email(self):
        self.user = UserFactory.create()
        EmailAddress.objects.create(
            user=self.user,
            email='miles2@davis.co',
            verified=False,
            primary=True
        )
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.render_content(emails_to_verify=True)

    def test_get_profile_with_verified_email(self):
        self.user = UserFactory.create()
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_update_profile(self):
        user = UserFactory.create(username='John',
                                  password='sgt-pepper')
        post_data = {
            'username': 'John',
            'email': user.email,
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en',
            'measurement': 'metric'
        }
        response = self.request(method='POST', post_data=post_data, user=user)
        response.status_code == 200

        user.refresh_from_db()
        assert user.full_name == 'John Lennon'

    def test_get_profile_when_no_user_is_signed_in(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_update_profile_when_no_user_is_signed_in(self):
        response = self.request(method='POST', post_data={})
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_update_profile_duplicate_email(self):
        user1 = UserFactory.create(username='John',
                                   full_name='John Lennon')
        user2 = UserFactory.create(username='Bill')
        post_data = {
            'username': 'Bill',
            'email': user1.email,
            'full_name': 'Bill Bloggs',
        }

        response = self.request(method='POST', user=user2, post_data=post_data)
        assert 'Failed to update profile information' in response.messages


class PasswordChangeTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PasswordChangeView
    success_url = reverse_lazy('account:profile')

    def setup_template_context(self):
        return {
            'form': ChangePasswordForm(instance=self.user)
        }

    def test_password_change(self):
        self.user = UserFactory.create(password='Noonewillguess!')
        data = {'oldpassword': 'Noonewillguess!',
                'password': 'Someonemightguess?'}
        response = self.request(method='POST', post_data=data, user=self.user)

        assert response.status_code == 302
        assert response.location == self.expected_success_url
        assert self.user.check_password('Someonemightguess?') is True


class LoginTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountLogin

    def setup_models(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk',
                                       password='iloveyoko79')

    def test_successful_login(self):
        data = {'login': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'dashboard' in response.location

    def test_successful_login_with_unverified_user(self):
        self.user.verify_email_by = datetime.datetime.now()
        self.user.save()

        data = {'login': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'account/inactive' in response.location
        assert len(mail.outbox) == 1
        self.user.refresh_from_db()
        assert self.user.is_active is False


class ConfirmEmailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ConfirmEmail
    url_kwargs = {'key': '123'}

    def setup_models(self):
        self.user = UserFactory.create(email='john@example.com')
        self.email_address = EmailAddress.objects.create(
            user=self.user,
            email='john@example.com',
            verified=False,
            primary=True
        )
        self.confirmation = EmailConfirmation.objects.create(
            email_address=self.email_address,
            sent=datetime.datetime.now(),
            key='123'
        )

    def test_activate(self):
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert 'dashboard' in response.location

        self.user.refresh_from_db()
        assert self.user.email_verified is True
        assert self.user.is_active is True

        self.email_address.refresh_from_db()
        assert self.email_address.verified is True

    def test_activate_changed_email(self):
        self.email_address.email = 'john2@example.com'
        self.email_address.save()

        EmailConfirmation.objects.create(
            email_address=self.email_address,
            sent=datetime.datetime.now(),
            key='456'
        )
        response = self.request(user=self.user, url_kwargs={'key': '456'})
        assert response.status_code == 302
        assert 'dashboard' in response.location

        self.user.refresh_from_db()
        assert self.user.email_verified is True
        assert self.user.is_active is True
        assert self.user.email == 'john2@example.com'

        self.email_address.refresh_from_db()
        assert self.email_address.verified is True

    def test_activate_with_invalid_token(self):
        response = self.request(user=self.user, url_kwargs={'key': 'abc'})
        assert response.status_code == 200

        self.user.refresh_from_db()
        assert self.user.email_verified is False
        assert self.user.is_active is True

        self.email_address.refresh_from_db()
        assert self.email_address.verified is False


class PasswordResetViewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PasswordResetView

    def setup_models(self):
        self.user = UserFactory.create(email='john@example.com')

    def test_mail_sent(self):
        data = {'email': 'john@example.com'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert len(mail.outbox) == 1

    def test_mail_not_sent(self):
        data = {'email': 'abcd@example.com'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert len(mail.outbox) == 0


class AccountListProjectsTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountListProjects
    template = 'accounts/user_dashboard.html'

    def test_without_organizations(self):
        user = UserFactory.create()

        response = self.request(user=user)

        assert response.status_code == 200
        assert response.content == self.render_content(
            user_orgs_and_projects=[])

    def test_with_organizations_without_projects(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()
        orgrole = OrganizationRole.objects.create(organization=org, user=user)

        response = self.request(user=user)

        assert response.status_code == 200
        assert response.content == self.render_content(
            user_orgs_and_projects=[(org, orgrole.admin, [])])

    def test_with_organizations_and_projects(self):
        user = UserFactory.create()
        org1, org2 = OrganizationFactory.create_batch(2)

        proj1, proj2 = ProjectFactory.create_batch(2, organization=org1)
        proj3 = ProjectFactory.create(organization=org2)
        proj4 = ProjectFactory.create(organization=org2, archived=False)

        ProjectRole.objects.create(project=proj1, user=user, role='DC')
        is_not_admin_org1 = OrganizationRole.objects.create(
            organization=org1, user=user, admin=False).admin
        is_admin_org2 = OrganizationRole.objects.create(
            organization=org2, user=user, admin=True).admin

        response = self.request(user=user)

        assert response.status_code == 200
        assert response.content == self.render_content(
            user_orgs_and_projects=[
                (org1, is_not_admin_org1, [
                    (proj1, 'Data Collector'),
                    (proj2, 'Public User')]),
                (org2, is_admin_org2, [
                    (proj3, 'Administrator'),
                    (proj4, 'Administrator')]),
                ])
