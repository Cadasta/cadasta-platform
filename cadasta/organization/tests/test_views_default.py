import json
from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.template import RequestContext

from tutelary.models import Policy, assign_user_policies

from accounts.tests.factories import UserFactory
from ..views import default
from ..models import Organization, OrganizationRole
from .. import forms
from .factories import OrganizationFactory, ProjectFactory, clause


class OrganizationListTest(TestCase):
    def setUp(self):
        self.view = default.OrganizationList.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.orgs = OrganizationFactory.create_batch(2)
        OrganizationFactory.create(**{'slug': 'unauthorized'})

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

    def test_get_with_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        response = self.view(self.request).render()
        content = response.content.decode('utf-8')

        expected = render_to_string(
            'organization/organization_list.html',
            {'object_list': self.orgs,
             'user': self.request.user})

        assert response.status_code == 200
        assert expected == content


class OrganizationAddTest(TestCase):
    def setUp(self):
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

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        response = self.view(self.request).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['form'] = forms.OrganizationForm()

        expected = render_to_string(
            'organization/organization_add.html',
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
            'url': 'http://example.com'
        })

        response = self.view(self.request)

        assert Organization.objects.count() == 1
        org = Organization.objects.first()

        assert response.status_code == 302
        assert '/organizations/{}/'.format(org.slug) in response['location']

    # def test_get_with_unauthorized_user(self):
    #     user = UserFactory.create()
    #     setattr(self.request, 'user', user)
    #     response = self.view(self.request).render()
    #     content = response.content.decode('utf-8')

    #     context = RequestContext(self.request)
    #     context['form'] = forms.OrganizationForm()

    #     expected = render_to_string(
    #         'organization/organization_add.html',
    #         context
    #     )

    #     assert response.status_code == 200
    #     assert expected == content



class OrganizationDashboardTest(TestCase):
    def setUp(self):
        self.view = default.OrganizationDashboard.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.org = OrganizationFactory.create()

        clauses = {
            'clause': [
                clause('allow', ['org.list']),
                clause('allow', ['org.view'], ['organization/*'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        response = self.view(self.request, slug=self.org.slug).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['object'] = self.org
        expected = render_to_string(
            'organization/organization_dashboard.html',
            context
        )

        assert response.status_code == 200
        assert expected == content

    # def test_get_with_unauthorized_user(self):
    #     assert False, 'Implement this'


class OrganzationEditTest(TestCase):
    def setUp(self):
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

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['form'] = forms.OrganizationForm(instance=self.org)
        context['object'] = self.org

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
            'urls': 'http://example.com'
        })

        response = self.view(self.request, slug=self.org.slug)

        self.org.refresh_from_db()

        assert response.status_code == 302
        assert ('/organizations/{}/'.format(self.org.slug)
                in response['location'])

        assert self.org.name == 'Org'
        assert self.org.description == 'Some description'


class OrganzationArchiveTest(TestCase):
    def setUp(self):
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


class OrganizationMembersTest(TestCase):
    def setUp(self):
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

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['object'] = self.org

        expected = render_to_string(
            'organization/organization_members.html',
            context
        )

        assert response.status_code == 200
        assert expected == content


class OrganizationMembersAddTest(TestCase):
    def setUp(self):
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

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(self.request, slug=self.org.slug).render()
        content = response.content.decode('utf-8')

        context = RequestContext(self.request)
        context['object'] = self.org
        context['form'] = forms.AddOrganizationMemberForm()

        expected = render_to_string(
            'organization/organization_members_add.html',
            context
        )

        assert response.status_code == 200
        assert expected == content

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
                    self.org.slug, user_to_add.username)
                in response['location'])
        assert OrganizationRole.objects.filter(
            organization=self.org, user=user_to_add).count() == 1


class OrganizationMembersEditTest(TestCase):
    def setUp(self):
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
        context['form'] = forms.EditOrganizationMemberForm(None, self.org, self.member)

        expected = render_to_string(
            'organization/organization_members_edit.html',
            context
        )

        assert response.status_code == 200
        assert expected == content

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


class OrganizationMembersRemoveTest(TestCase):
    def setUp(self):
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

    def test_get_with_authorized_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)

        response = self.view(
            self.request,
            slug=self.org.slug,
            username=self.member.username)

        assert response.status_code == 302
        assert ('/organizations/{}/members/'.format(self.org.slug)
                in response['location'])
        assert (OrganizationRole.objects.filter(organization=self.org,
                                                user=self.member).exists() is
                False)


class ProjectListTest(TestCase):
    def setUp(self):
        self.view = default.ProjectList.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

        self.ok_org1 = OrganizationFactory.create(
            name='OK org 1', slug='org1'
        )
        self.ok_org2 = OrganizationFactory.create(
            name='OK org 2', slug='org2'
        )
        self.unath_org = OrganizationFactory.create(
            name='Unauthorized org', slug='unauth-org'
        )
        self.projs = []
        self.projs += ProjectFactory.create_batch(2, organization=self.ok_org1)
        self.projs += ProjectFactory.create_batch(2, organization=self.ok_org2)
        ProjectFactory.create(
            name='Unauthorized project',
            project_slug='unauth-proj',
            organization=self.ok_org2
        )
        ProjectFactory.create(
            name='Project in unauthorized org',
            project_slug='proj-in-unath-org',
            organization=self.unath_org
        )

        clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*']),
                clause('deny',  ['project.view'], ['project/unauth-org/*']),
                clause('deny',  ['project.view'], ['project/*/unauth-proj'])
            ]
        }
        self.policy = Policy.objects.create(
            name='allow',
            body=json.dumps(clauses))

    def test_get_with_user(self):
        user = UserFactory.create()
        assign_user_policies(user, self.policy)
        setattr(self.request, 'user', user)
        response = self.view(self.request).render()
        content = response.content.decode('utf-8')

        expected = render_to_string(
            'organization/project_list.html',
            {'object_list': self.projs,
             'add_allowed': True,
             'user': self.request.user})

        assert response.status_code == 200
        assert expected == content


class ProjectAddTest(TestCase):
    pass
