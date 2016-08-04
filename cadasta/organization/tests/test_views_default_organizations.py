import json

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser

from tutelary.models import Policy, Role, assign_user_policies
from skivvy import ViewTestCase

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from ..views import default
from ..models import Organization, OrganizationRole, Project
from .. import forms
from .factories import OrganizationFactory, ProjectFactory, clause


def assign_policies(user):
    clauses = {
        'clause': [
            clause('allow', ['org.list']),
            clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
        ]
    }
    policy = Policy.objects.create(
        name='allow',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class OrganizationListTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationList
    template = 'organization/organization_list.html'

    def setup_models(self):
        self.orgs = OrganizationFactory.create_batch(2)
        unauthorized = OrganizationFactory.create(slug='unauthorized')
        self.all_orgs = self.orgs + [unauthorized]

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*']),
                clause('deny', ['org.view'], ['organization/unauthorized'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assigned_policies = self.user.assigned_policies()
        assigned_policies.append(self.policy)
        self.user.assign_policies(*assigned_policies)

    def setup_template_context(self):
        return {
            'object_list': sorted(self.all_orgs, key=lambda p: p.slug),
            'user': self.user,
            'is_superuser': False
        }

    def test_get_with_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.render_content(
            object_list=sorted(self.orgs, key=lambda p: p.slug))

    def test_get_without_user(self):
        response = self.request()
        assert response.status_code == 200
        assert response.content == self.render_content(user=AnonymousUser())

    def test_get_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)
        response = self.request(user=superuser)
        assert response.status_code == 200
        assert response.content == self.render_content(user=superuser,
                                                       is_superuser=True)


class OrganizationAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationAdd
    template = 'organization/organization_add.html'
    template_context = {'form': forms.OrganizationForm()}

    def setup_models(self):
        clauses = {
            'clause': [
                clause('allow', ['org.create'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, self.policy)

    def setup_post_data(self):
        return {
            'name': 'Org',
            'description': 'Some description',
            'url': 'http://example.com',
            'contacts-TOTAL_FORMS': '1',
            'contacts-INITIAL_FORMS': '0',
            'contacts-MAX_NUM_FORMS': '0',
            'contact-0-name': '',
            'contact-0-email': '',
            'contact-0-tel': '',
        }

    def test_get_with_authorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 302
        assert Organization.objects.count() == 1
        org = Organization.objects.first()
        assert '/organizations/{}/'.format(org.slug) in response.location
        assert OrganizationRole.objects.get(
            organization=org, user=self.user
        ).admin

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        assert response.status_code == 302
        assert Organization.objects.count() == 0
        assert '/account/login/' in response.location


class OrganizationDashboardTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationDashboard
    template = 'organization/organization_dashboard.html'

    def setup_models(self):
        self.org = OrganizationFactory.create()
        self.projs = ProjectFactory.create_batch(2, organization=self.org)
        self.private_proj = ProjectFactory.create(
            organization=self.org, access='private')
        self.all_projects = self.projs + [self.private_proj]

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        self.user = UserFactory.create()

    def setup_url_kwargs(self):
        return {'slug': self.org.slug}

    def setup_template_context(self):
        return {
            'organization': self.org,
            'projects': self.projs,
            'is_superuser': False,
            'add_allowed': False,
            'is_administrator': False
        }

    def test_get_org_with_authorized_user(self):
        assign_user_policies(self.user, self.policy)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_org_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_org_with_org_membership(self):
        OrganizationRole.objects.create(organization=self.org, user=self.user)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content == self.render_content(
            projects=Project.objects.all())

    def test_get_org_with_new_org(self):
        new_org = OrganizationFactory.create()
        assign_user_policies(self.user, self.policy)
        response = self.request(user=self.user,
                                url_kwargs={'slug': new_org.slug})
        assert response.status_code == 200
        assert response.content == self.render_content(organization=new_org,
                                                       projects=[])

    def test_get_org_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)
        response = self.request(user=superuser)
        assert response.status_code == 200
        assert response.content == self.render_content(
            member=True,
            is_superuser=True,
            is_administrator=True,
            add_allowed=True,
            projects=self.all_projects)

    def test_get_org_with_org_admin(self):
        org_admin = UserFactory.create()
        OrganizationRole.objects.create(
            organization=self.org,
            user=org_admin,
            admin=True
        )
        response = self.request(user=org_admin)
        assert response.status_code == 200
        assert response.content == self.render_content(
            member=True,
            is_superuser=False,
            is_administrator=True,
            add_allowed=True,
            projects=self.all_projects)


class OrganizationEditTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationEdit
    template = 'organization/organization_edit.html'
    post_data = {
        'name': 'Org',
        'description': 'Some description',
        'urls': 'http://example.com',
        'contacts-TOTAL_FORMS': '1',
        'contacts-INITIAL_FORMS': '0',
        'contacts-MAX_NUM_FORMS': '0',
        'contact-0-name': '',
        'contact-0-email': '',
        'contact-0-tel': '',
    }

    def setup_models(self):
        self.org = OrganizationFactory.create()

    def setup_url_kwargs(self):
        return {'slug': self.org.slug}

    def setup_template_context(self):
        return {
            'form': forms.OrganizationForm(instance=self.org),
            'organization': self.org
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)

        assert response.status_code == 302
        assert ("You don't have permission to update this organization"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ('/organizations/{}/'.format(self.org.slug)
                in response.location)

        self.org.refresh_from_db()

        assert self.org.name == 'Org'
        assert self.org.description == 'Some description'

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()

        response = self.request(method='POST', user=user)
        assert response.status_code == 302
        assert ("You don't have permission to update this organization"
                in response.messages)
        assert self.org.name != 'Org'
        assert self.org.description != 'Some description'

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.org.name != 'Org'
        assert self.org.description != 'Some description'


class OrganizationArchiveTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationArchive

    def setup_models(self):
        self.org = OrganizationFactory.create()

    def setup_url_kwargs(self):
        return {'slug': self.org.slug}

    def test_archive_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/'.format(self.org.slug)
                in response.location)
        assert self.org.archived is True

    def test_archive_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)

        self.org.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to archive this organization"
                in response.messages)
        assert self.org.archived is False

    def test_archive_with_unauthenticated_user(self):
        response = self.request()
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.org.archived is False


class OrganizationUnarchiveTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationUnarchive

    def setup_models(self):
        self.view = default.OrganizationUnarchive.as_view()
        self.org = OrganizationFactory.create(archived=True)

    def setup_url_kwargs(self):
        return {'slug': self.org.slug}

    def test_unarchive_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)

        response = self.request(user=user)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/'.format(self.org.slug)
                in response.location)
        assert self.org.archived is False

    def test_unarchive_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)

        self.org.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to unarchive this organization"
                in response.messages)
        assert self.org.archived is True

    def test_unarchive_with_unauthenticated_user(self):
        response = self.request()
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert self.org.archived is True


class OrganizationMembersTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationMembers
    template = 'organization/organization_members.html'

    def setup_models(self):
        self.users = UserFactory.create_batch(2)
        self.org = OrganizationFactory.create(add_users=self.users)

    def setup_template_context(self):
        return {'organization': self.org}

    def setup_url_kwargs(self):
        return {'slug': self.org.slug}

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)

        assert response.status_code == 302
        assert ("You don't have permission to view members of this "
                "organization"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()

        assert response.status_code == 302
        assert '/account/login/' in response.location


class OrganizationMembersAddTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationMembersAdd
    template = 'organization/organization_members_add.html'
    post_data = {'identifier': 'add_me'}

    def setup_models(self):
        self.org = OrganizationFactory.create()

    def setup_url_kwargs(self):
        return {'slug': self.org.slug}

    def setup_template_context(self):
        return {
            'organization': self.org,
            'form': forms.AddOrganizationMemberForm()
        }

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert ("You don't have permission to add members to this organization"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()

        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        user_to_add = UserFactory.create(username='add_me')
        assign_policies(user)

        response = self.request(method='POST', user=user)

        assert response.status_code == 302
        assert ('/organizations/{}/members/{}'.format(
            self.org.slug, user_to_add.username) in response.location
        )
        assert OrganizationRole.objects.filter(
            organization=self.org, user=user_to_add).exists() is True

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        user_to_add = UserFactory.create(username='add_me')
        response = self.request(method='POST', user=user)

        assert response.status_code == 302
        assert ("You don't have permission to add members to this organization"
                in response.messages)
        assert OrganizationRole.objects.filter(
            organization=self.org, user=user_to_add).exists() is False

    def test_post_with_unauthenticated_user(self):
        user_to_add = UserFactory.create(username='add_me')
        response = self.request(method='POST')

        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert OrganizationRole.objects.filter(
            organization=self.org, user=user_to_add).exists() is False


class OrganizationMembersEditTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationMembersEdit
    template = 'organization/organization_members_edit.html'
    post_data = {'org_role': 'A'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.member = UserFactory.create()
        self.org = OrganizationFactory.create(add_users=[self.member])

    def setup_url_kwargs(self):
        return {'slug': self.org.slug, 'username': self.member.username}

    def setup_template_context(self):
        return {
            'object': self.member,
            'organization': self.org,
            'form': forms.EditOrganizationMemberForm(
                None, self.org, self.member, self.user)
        }

    def test_get_with_authorized_user(self):
        OrganizationRole.objects.create(organization=self.org, user=self.user)
        assign_policies(self.user)
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_with_unauthorized_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert ("You don't have permission to edit roles of this organization"
                in response.messages)

    def test_get_with_unauthenticated_user(self):
        response = self.request()

        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_post_with_authorized_user(self):
        assign_policies(self.user)
        response = self.request(method='POST', user=self.user)

        assert response.status_code == 302
        assert ('/organizations/{}/members/'.format(self.org.slug)
                in response.location)
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.member)
        assert role.admin is True

    def test_post_with_unauthorized_user(self):
        self.user = UserFactory.create()
        response = self.request(method='POST', user=self.user)

        assert response.status_code == 302
        assert ("You don't have permission to edit roles of this organization"
                in response.messages)
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.member)
        assert role.admin is False

    def test_post_with_unauthenticated_user(self):
        response = self.request(method='POST')

        assert response.status_code == 302
        assert '/account/login/' in response.location
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.member)
        assert role.admin is False

    def test_post_with_invalid_form(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org, user=user)
        assign_policies(user)
        response = self.request(method='POST', user=user,
                                post_data={'org_role': 'X'})

        form = forms.EditOrganizationMemberForm(
                {'org_role': 'X'}, self.org, self.member, self.user)
        assert response.status_code == 200
        assert response.content == self.render_content(form=form)


class OrganizationMembersRemoveTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.OrganizationMembersRemove

    def setup_models(self):
        self.member = UserFactory.create()
        self.org = OrganizationFactory.create(add_users=[self.member])

    def setup_url_kwargs(self):
        return {'slug': self.org.slug, 'username': self.member.username}

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_policies(user)
        response = self.request(user=user)

        role = OrganizationRole.objects.filter(organization=self.org,
                                               user=self.member).exists()

        assert response.status_code == 302
        assert ('/organizations/{}/members/'.format(self.org.slug)
                in response.location)
        assert role is False

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)

        role = OrganizationRole.objects.filter(organization=self.org,
                                               user=self.member).exists()
        assert response.status_code == 302
        assert ("You don't have permission to remove members from this "
                "organization"
                in response.messages)
        assert role is True

    def test_get_with_unauthenticated_user(self):
        response = self.request()
        role = OrganizationRole.objects.filter(organization=self.org,
                                               user=self.member).exists()

        assert response.status_code == 302
        assert '/account/login/' in response.location
        assert role is True
