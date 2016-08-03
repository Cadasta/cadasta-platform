import json

from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages.api import get_messages

from tutelary.models import Policy, Role, assign_user_policies

from core.tests.base_test_case import UserTestCase
from accounts.tests.factories import UserFactory
from ..views import default
from ..models import Organization, OrganizationRole, Project
from .. import forms
from .factories import OrganizationFactory, ProjectFactory, clause


class OrganizationListTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationList.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        self.orgs = OrganizationFactory.create_batch(2)
        OrganizationFactory.create(slug='unauthorized')

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

    def _get(self, orgs, user=None, status=None,
             make_org_member=None, is_superuser=False):
        if user is None:
            user = self.user
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        if status is not None:
            assert response.status_code == status
        content = response.render().content.decode('utf-8')

        expected = render_to_string(
            'organization/organization_list.html',
            {'object_list': sorted(orgs, key=lambda p: p.slug),
             'user': self.request.user,
             'is_superuser': is_superuser},
            request=self.request)

        if expected != content:
            with open('expected.txt', 'w') as fp:
                print(expected, file=fp)
            with open('content.txt', 'w') as fp:
                print(content, file=fp)
        assert expected == content

    def test_get_with_user(self):
        self._get(self.orgs, status=200)

    def test_get_without_user(self):
        self._get(Organization.objects.all(), user=AnonymousUser(), status=200)

    def test_get_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)
        self._get(Organization.objects.all(),
                  user=superuser, is_superuser=True,
                  status=200)


class OrganizationAddTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationAdd.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

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

    def _get(self, status=None):
        response = self.view(self.request)
        if status is not None:
            assert response.status_code == status
        return response

    def _post(self, status=None, count=None):
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {
            'name': 'Org',
            'description': 'Some description',
            'url': 'http://example.com',
            'contacts-TOTAL_FORMS': '1',
            'contacts-INITIAL_FORMS': '0',
            'contacts-MAX_NUM_FORMS': '0',
            'contact-0-name': '',
            'contact-0-email': '',
            'contact-0-tel': '',
        })
        response = self.view(self.request)
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert Organization.objects.count() == count
        return response

    def test_get_with_authorized_user(self):
        setattr(self.request, 'user', self.user)
        response = self._get(status=200).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['form'] = forms.OrganizationForm()

        expected = render_to_string(
            'organization/organization_add.html',
            context
        )

        assert expected == content

    def test_post_with_authorized_user(self):
        setattr(self.request, 'user', self.user)
        response = self._post(status=302, count=1)
        org = Organization.objects.first()
        assert '/organizations/{}/'.format(org.slug) in response['location']
        assert OrganizationRole.objects.get(
            organization=org, user=self.user
        ).admin

    def test_get_with_unauthenticated_user(self):
        response = self._get(status=302)
        assert '/account/login/' in response['location']

    def test_post_with_unauthenticated_user(self):
        response = self._post(status=302, count=0)
        assert '/account/login/' in response['location']


class OrganizationDashboardTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationDashboard.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')

        self.org = OrganizationFactory.create()
        self.projs = ProjectFactory.create_batch(2, organization=self.org)
        self.private_proj = ProjectFactory.create(
            organization=self.org, access='private')

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        self.user = UserFactory.create()
        setattr(self.request, 'user', self.user)

        self.org_admin = UserFactory.create()
        OrganizationRole.objects.create(
            organization=self.org,
            user=self.org_admin,
            admin=True
        )

    def _get(self, slug, status=None, user=None, make_org_member=None,):
        if user is None:
            user = self.user
        if make_org_member is not None:
            OrganizationRole.objects.create(organization=self.org, user=user)
        setattr(self.request, 'user', user)
        response = self.view(self.request, slug=slug)
        if status is not None:
            assert response.status_code == status
        return response

    def _check_ok(self, response, org=None, member=False,
                  is_superuser=False, is_administrator=None):
        content = response.render().content.decode('utf-8')

        context = RequestContext(self.request)
        org = org or self.org
        context['organization'] = org
        if member:
            context['projects'] = Project.objects.filter(
                organization__slug=org.slug)
        else:
            context['projects'] = Project.objects.filter(
                organization__slug=org.slug, access='public')
        context['is_superuser'] = is_superuser
        if is_administrator is None:
            is_administrator = is_superuser
        context['add_allowed'] = is_administrator
        context['is_administrator'] = is_administrator

        expected = render_to_string(
            'organization/organization_dashboard.html',
            context
        )

        assert expected == content

    def test_get_org_with_authorized_user(self):
        assign_user_policies(self.user, self.policy)
        response = self._get(self.org.slug, status=200)
        self._check_ok(response)

    def test_get_org_with_unauthorized_user(self):
        response = self._get(self.org.slug, user=AnonymousUser(), status=200)
        self._check_ok(response)

    def test_get_org_with_org_membership(self):
        response = self._get(
            self.org.slug, status=200, make_org_member=self.org)
        self._check_ok(response, member=True)

    def test_get_org_with_new_org(self):
        new_org = OrganizationFactory.create()
        assign_user_policies(self.user, self.policy)
        response = self._get(new_org.slug, status=200)
        self._check_ok(response, org=new_org)

    def test_get_org_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)
        response = self._get(self.org.slug, user=superuser, status=200)
        self._check_ok(response, member=True, is_superuser=True)

    def test_get_org_with_org_admin(self):
        response = self._get(self.org.slug, user=self.org_admin, status=200)
        self._check_ok(response, member=True, is_administrator=True)


class OrganizationEditTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationEdit.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.org = OrganizationFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.*'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['form'] = forms.OrganizationForm(instance=self.org)
        context['organization'] = self.org

        expected = render_to_string(
            'organization/organization_edit.html',
            context
        )

        assert response.status_code == 200
        assert expected == content

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {
            'name': 'Org',
            'description': 'Some description',
            'urls': 'http://example.com',
            'contacts-TOTAL_FORMS': '1',
            'contacts-INITIAL_FORMS': '0',
            'contacts-MAX_NUM_FORMS': '0',
            'contact-0-name': '',
            'contact-0-email': '',
            'contact-0-tel': '',
        })

        response = self.view(self.request, slug=self.org.slug)

        self.org.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/'.format(self.org.slug)
                in response['location'])

        assert self.org.name == 'Org'
        assert self.org.description == 'Some description'

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request, slug=self.org.slug)

        assert response.status_code == 302
        assert ("You don't have permission to update this organization"
                in [str(m) for m in get_messages(self.request)])

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)

        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {
            'name': 'Org',
            'description': 'Some description',
            'urls': 'http://example.com'
        })

        response = self.view(self.request, slug=self.org.slug)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert ("You don't have permission to update this organization"
                in [str(m) for m in get_messages(self.request)])
        assert self.org.name != 'Org'
        assert self.org.description != 'Some description'

    def test_get_with_unauthenticated_user(self):
        response = self.view(self.request)
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_unauthenticated_user(self):
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {
            'name': 'Org',
            'description': 'Some description',
            'urls': 'http://example.com'
        })

        response = self.view(self.request, slug=self.org.slug)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert self.org.name != 'Org'
        assert self.org.description != 'Some description'


class OrganizationArchiveTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationArchive.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.org = OrganizationFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.*'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_archive_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/'.format(self.org.slug)
                in response['location'])
        assert self.org.archived is True

    def test_archive_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request, slug=self.org.slug)

        self.org.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to archive this organization"
                in [str(m) for m in get_messages(self.request)])
        assert self.org.archived is False

    def test_archive_with_unauthenticated_user(self):
        response = self.view(self.request)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert self.org.archived is False


class OrganizationUnarchiveTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationUnarchive.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.org = OrganizationFactory.create(archived=True)

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.*'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_unarchive_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/'.format(self.org.slug)
                in response['location'])
        assert self.org.archived is False

    def test_unarchive_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request, slug=self.org.slug)

        self.org.refresh_from_db()
        assert response.status_code == 302
        assert ("You don't have permission to unarchive this organization"
                in [str(m) for m in get_messages(self.request)])
        assert self.org.archived is True

    def test_unarchive_with_unauthenticated_user(self):
        response = self.view(self.request)
        self.org.refresh_from_db()

        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert self.org.archived is True


class OrganizationMembersTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationMembers.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.users = UserFactory.create_batch(2)
        self.org = OrganizationFactory.create(add_users=self.users)

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['organization'] = self.org

        expected = render_to_string(
            'organization/organization_members.html',
            context
        )

        assert response.status_code == 200
        assert expected == content

        response = self.view(self.request, slug=self.org.slug)

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug)
        assert response.status_code == 302
        assert ("You don't have permission to view members of this "
                "organization"
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.view(self.request)

        assert response.status_code == 302
        assert '/account/login/' in response['location']


class OrganizationMembersAddTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationMembersAdd.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.org = OrganizationFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['organization'] = self.org
        context['form'] = forms.AddOrganizationMemberForm()

        expected = render_to_string(
            'organization/organization_members_add.html',
            context
        )

        assert response.status_code == 200
        assert expected == content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug)
        assert response.status_code == 302
        assert ("You don't have permission to add members to this organization"
                in [str(m) for m in get_messages(self.request)])

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        user_to_add = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {'identifier': user_to_add.username})

        response = self.view(self.request, slug=self.org.slug)

        assert response.status_code == 302
        assert ('/organizations/{}/members/{}'.format(
            self.org.slug, user_to_add.username) in response['location']
        )
        assert OrganizationRole.objects.filter(
            organization=self.org, user=user_to_add).exists() is True

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        user_to_add = UserFactory.create()
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {'identifier': user_to_add.username})

        response = self.view(self.request, slug=self.org.slug)

        assert response.status_code == 302
        assert ("You don't have permission to add members to this organization"
                in [str(m) for m in get_messages(self.request)])
        assert OrganizationRole.objects.filter(
            organization=self.org, user=user_to_add).exists() is False

    def test_get_with_unauthenticated_user(self):
        response = self.view(self.request, slug=self.org.slug)

        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_unauthenticated_user(self):
        user_to_add = UserFactory.create()
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {'identifier': user_to_add.username})

        response = self.view(self.request, slug=self.org.slug)
        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert OrganizationRole.objects.filter(
            organization=self.org, user=user_to_add).exists() is False


class OrganizationMembersEditTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationMembersEdit.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.member = UserFactory.create()
        self.org = OrganizationFactory.create(add_users=[self.member])

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['object'] = self.member
        context['organization'] = self.org
        context['form'] = forms.EditOrganizationMemberForm(
            None, self.org, self.member)
        context['user'] = self.member

        expected = render_to_string(
            'organization/organization_members_edit.html',
            context
        )

        assert response.status_code == 200
        assert expected == content

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username)
        assert response.status_code == 302
        assert ("You don't have permission to edit roles of this organization"
                in [str(m) for m in get_messages(self.request)])

    def test_get_with_unauthenticated_user(self):
        response = self.view(self.request, slug=self.org.slug)

        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_post_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {'org_role': 'A'})

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username)

        assert response.status_code == 302
        assert ('/organizations/{}/members/'.format(self.org.slug)
                in response['location'])
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.member)
        assert role.admin is True

    def test_post_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {'org_role': 'A'})

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username)

        assert response.status_code == 302
        assert ("You don't have permission to edit roles of this organization"
                in [str(m) for m in get_messages(self.request)])
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.member)
        assert role.admin is False

    def test_post_with_unauthenticated_user(self):
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {'org_role': 'A'})

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username)

        assert response.status_code == 302
        assert '/account/login/' in response['location']
        role = OrganizationRole.objects.get(organization=self.org,
                                            user=self.member)
        assert role.admin is False

    def test_post_with_invalid_form(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        setattr(self.request, 'method', 'POST')
        setattr(self.request, 'POST', {'org_role': 'X'})

        response = self.view(self.request, slug=self.org.slug,
                             username=self.member.username).render()
        assert response.status_code == 200
        errors = response.context_data['form']['org_role'].errors
        assert len(errors) == 1
        assert 'X is not one of the available choices' in errors[0]


class OrganizationMembersRemoveTest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = default.OrganizationMembersRemove.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.member = UserFactory.create()
        self.org = OrganizationFactory.create(add_users=[self.member])

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.*', 'org.*.*'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username)
        role = OrganizationRole.objects.filter(organization=self.org,
                                               user=self.member).exists()

        assert response.status_code == 302
        assert ('/organizations/{}/members/'.format(self.org.slug)
                in response['location'])
        assert role is False

    def test_get_with_unauthorized_user(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username)
        role = OrganizationRole.objects.filter(organization=self.org,
                                               user=self.member).exists()
        assert response.status_code == 302
        assert ("You don't have permission to remove members from this "
                "organization"
                in [str(m) for m in get_messages(self.request)])
        assert role is True

    def test_get_with_unauthenticated_user(self):
        response = self.view(self.request, slug=self.org.slug)
        role = OrganizationRole.objects.filter(organization=self.org,
                                               user=self.member).exists()

        assert response.status_code == 302
        assert '/account/login/' in response['location']
        assert role is True
