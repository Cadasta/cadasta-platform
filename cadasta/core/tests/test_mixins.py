import pytest

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from core.roles import AnonymousUserRole
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.test import TestCase, RequestFactory
from django.views import generic
from rest_framework import generics as generic_api
from rest_framework import exceptions as api_exceptions
from rest_framework.test import APIRequestFactory, force_authenticate
from jsonattrs.models import Attribute, Schema
from organization.tests.factories import OrganizationFactory, ProjectFactory
from organization.views import default as org_views

from questionnaires.models import Questionnaire
from spatial.views.default import LocationsAdd
from organization.views.default import OrganizationEdit
from organization.models import OrganizationRole, ProjectRole

from ..mixins import (SchemaSelectorMixin, RolePermissionRequiredMixin,
                      PermissionFilterMixin, APIPermissionRequiredMixin)


# Tutelary mixin test - to be removed
class PermissionRequiredMixinTest(UserTestCase, TestCase):

    def test_login_redirect_to_original_referer(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        view = LocationsAdd.as_view()

        request = HttpRequest()
        referer = '/organizations/{}/projects/{}'.format(
            project.organization.slug,
            project.slug
        )
        request.META['HTTP_REFERER'] = referer
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {
            'organization': project.organization.slug,
            'project': project.slug
        }

        response = view(request, **kwargs)
        assert response.status_code == 302
        assert referer == response['location']

    def test_login_redirect_to_project_dashboard(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        view = LocationsAdd.as_view()

        request = HttpRequest()
        request.META['HTTP_REFERER'] = '/account/login/'
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {
            'organization': project.organization.slug,
            'project': project.slug
        }

        exp_redirect = reverse('organization:project-dashboard', kwargs=kwargs)
        response = view(request, **kwargs)
        assert response.status_code == 302
        assert exp_redirect == response['location']


class RolePermissionRequiredMixinTest(UserTestCase, TestCase):

    def test_raise_improperly_configured(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user

        user1 = UserFactory.create()
        org = OrganizationFactory.create()
        with pytest.raises(ImproperlyConfigured):
            MockView(org, user1).has_permission()

    def test_has_permission_with_superuser(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user

        user = UserFactory.create(is_superuser=True)
        org = OrganizationFactory.create()
        assert MockView(org, user).has_permission()

    def test_get_permission_required_from_dict(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user
            permission_required = {'GET': 'some.permission'}

        user = UserFactory.create()
        org = OrganizationFactory.create()
        assert ('some.permission',) == MockView(
            org, user).get_permission_required()

    def test_get_queryset(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user

            def get_filtered_queryset(self):
                return []

        user = UserFactory.create()
        org = OrganizationFactory.create()
        assert [] == MockView(org, user).get_queryset()

    def test_set_anonymous_user_role(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user

        user = AnonymousUser()
        org = OrganizationFactory.create()
        view = MockView(org, user)
        view.set_user_roles()
        assert isinstance(view._roles[0], AnonymousUserRole)

    def test_set_organization_role(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user

            def get_organization(self):
                return self.obj

        user = UserFactory.create()
        org = OrganizationFactory.create()
        group = Group.objects.get(name='OrgMember')
        role = OrganizationRole.objects.create(
            organization=org, user=user, group=group)
        view = MockView(org, user)
        view.set_user_roles()
        assert view._roles[0] == role

    def test_get_org_role(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user

            def get_org_role(self):
                self._org_role = OrganizationRole.objects.get(
                    organization=self.obj, user=self.request.user)
                return self._org_role

        user = UserFactory.create()
        org = OrganizationFactory.create()
        group = Group.objects.get(name='OrgMember')
        role = OrganizationRole.objects.create(
            organization=org, user=user, group=group)
        view = MockView(org, user)
        view.set_user_roles()
        assert view._roles[0] == role

    def test_get_project_role(self):
        class MockView(RolePermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get('/check')
                self.request.user = user

            def get_prj_role(self):
                self._prj_role = ProjectRole.objects.get(
                    project=self.obj, user=self.request.user)
                return self._prj_role

        user = UserFactory.create()
        project = ProjectFactory.create()
        group = Group.objects.get(name='ProjectMember')
        role = ProjectRole.objects.create(
            project=project, user=user, group=group, role='PU')
        view = MockView(project, user)
        view.set_user_roles()
        assert view._roles[0] == role

    def test_login_redirect_from_project_dashboard_to_org_dashboard(self):
        user = UserFactory.create()
        project = ProjectFactory.create(access='private')

        view = org_views.ProjectDashboard.as_view()

        request = HttpRequest()
        request.META['HTTP_REFERER'] = '/account/login/'
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {
            'organization': project.organization.slug,
            'project': project.slug
        }

        def get_full_path():
            return '/organizations/{}/projects/{}/'.format(
                project.organization.slug,
                project.slug
            )
        setattr(request, 'get_full_path', get_full_path)

        exp_redirect = reverse('organization:dashboard', kwargs={
            'slug': project.organization.slug})
        response = view(request, **kwargs)
        assert response.status_code == 302
        assert exp_redirect == response['location']

    def test_login_redirect_to_organization_dashboard(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()

        view = org_views.OrganizationEdit.as_view()

        request = HttpRequest()
        request.META['HTTP_REFERER'] = '/account/login/'
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {'slug': org.slug}

        exp_redirect = reverse('organization:dashboard', kwargs=kwargs)
        response = view(request, **kwargs)
        assert response.status_code == 302
        assert exp_redirect == response['location']

    def test_login_redirect_from_org_dashboard_to_dashboard(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(access='private')
        view = org_views.OrganizationDashboard.as_view()

        request = HttpRequest()
        request.META['HTTP_REFERER'] = '/account/login/'
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {'slug': org.slug}

        def get_full_path():
            return '/organizations/{}/'.format(org.slug)
        setattr(request, 'get_full_path', get_full_path)

        exp_redirect = reverse('core:dashboard')
        response = view(request, **kwargs)
        assert response.status_code == 302
        assert exp_redirect == response['location']


class RoleLoginPermissionRequiredMixinTest(UserTestCase, TestCase):
    def test_login_redirect_to_original_referer(self):
        user = AnonymousUser()
        org = OrganizationFactory.create()

        view = OrganizationEdit.as_view()

        request = HttpRequest()
        referer = '/organizations/{}/'.format(org.slug)

        request.META['HTTP_REFERER'] = referer
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {'slug': org.slug}

        def get_full_path():
            return '/organizations/{}/'.format(org.slug)
        setattr(request, 'get_full_path', get_full_path)

        response = view(request, **kwargs)
        assert response.status_code == 302
        assert response['location'] == '/account/login/?next={}'.format(
            referer)

    def test_login_raise_exception(self):
        user = AnonymousUser()
        org = OrganizationFactory.create()
        setattr(OrganizationEdit, 'raise_exception', True)

        view = OrganizationEdit.as_view()

        request = HttpRequest()
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        kwargs = {'slug': org.slug}

        with pytest.raises(PermissionDenied) as e:
            view(request, **kwargs)
        assert str(e.value) == ("You don't have permission to "
                                "update this organization")
        delattr(OrganizationEdit, 'raise_exception')


class PermissionFilterMixinTest(UserTestCase, TestCase):

    def test_get_with_permissions(self):
        class MockView(PermissionFilterMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get(
                    '/check?permissions=org.create')
                self.request.user = user

            def get_object(self):
                return self.obj

            def permission_filter_queryset(self):
                return None

        user = UserFactory.create()
        project = ProjectFactory.create()
        view = MockView(project, user)
        view.dispatch(view.request)
        assert view.permission_filter == ('org.create',)

    def test_get_permission_filter_queryset(self):
        class MockView(PermissionFilterMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get(
                    '/check?permissions=org.create')
                self.request.user = user

            def permission_filter_queryset(self):
                return []

        user = UserFactory.create()
        project = ProjectFactory.create()
        view = MockView(project, user)
        assert [] == view.get_queryset()

    def test_get_filter_queryset(self):
        class MockMixin():
            def get_filtered_queryset(self):
                return []

        class MockView(PermissionFilterMixin, MockMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = RequestFactory().get(
                    '/check?permissions=org.create')
                self.request.user = user

        user = UserFactory.create()
        project = ProjectFactory.create()
        view = MockView(project, user)
        assert [] == view.get_queryset()


class APIPermissionRequiredMixinTest(UserTestCase, TestCase):
    def test_get_permission_denied(self):
        class MockAPIView(APIPermissionRequiredMixin, generic.DetailView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = APIRequestFactory().get('/check')
                self.request.user = user
            permission_denied_message = 'Permission denied'

        user = UserFactory.create()
        view = MockAPIView(None, user)
        assert view.get_permission_denied_message() == ('Permission denied',)

    def test_method_not_allowed(self):
        class MockAPIView(APIPermissionRequiredMixin,
                          generic_api.ListCreateAPIView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = APIRequestFactory().put('/check')
                self.request.user = user
            permission_denied_message = 'Permission denied'

        user = UserFactory.create(is_superuser=True)
        view = MockAPIView(None, user)
        with pytest.raises(api_exceptions.MethodNotAllowed) as e:
            view.check_permissions(view.request)
        assert str(e.value) == 'Method "PUT" not allowed.'

    def test_check_permissions_with_anonymous_user(self):
        class MockAPIView(APIPermissionRequiredMixin,
                          generic_api.ListCreateAPIView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = APIRequestFactory().post('/check')
                self.request.user = user
            permission_denied_message = 'Permission denied'

        user = AnonymousUser()
        view = MockAPIView(None, user)
        with pytest.raises(api_exceptions.NotAuthenticated) as e:
            view.check_permissions(view.request)
        assert str(e.value) == 'Authentication credentials were not provided.'

    def test_check_permissions_with_superuser(self):
        class MockAPIView(APIPermissionRequiredMixin,
                          generic_api.ListCreateAPIView):
            def __init__(self, obj, user):
                self.obj = obj
                self.request = APIRequestFactory().get('/check')
                self.request.user = user
            permission_denied_message = 'Permission denied'

        user = UserFactory.create(is_superuser=True)
        view = MockAPIView(None, user)
        assert view.check_permissions(view.request)

    def test_check_permissions_with_org_role(self):
        class MockAPIView(APIPermissionRequiredMixin,
                          generic_api.ListCreateAPIView):
            def __init__(self, obj, request, user):
                self.obj = obj
                self.request = request
                self.request.user = user
            permission_required = 'no.permission'
            permission_denied_message = 'Permission denied'

            def get_org_role(self):
                self._org_role = OrganizationRole.objects.get(
                    organization=self.obj, user=self.request.user)
                return self._org_role

            def permission_denied(self, request, message=None):
                raise api_exceptions.PermissionDenied(detail=message)

        request = APIRequestFactory().get('/check')
        user = UserFactory.create()
        force_authenticate(request, user=user)
        org = OrganizationFactory.create()
        group = Group.objects.get(name='OrgMember')
        OrganizationRole.objects.create(
            organization=org, user=user, group=group)
        view = MockAPIView(org, request, user)
        with pytest.raises(api_exceptions.PermissionDenied) as e:
            view.check_permissions(view.request)
        assert str(e.value) == 'Permission denied'


@pytest.mark.usefixtures('make_dirs')
class SchemaSelectorMixinTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        super().setUp()
        file = self.get_file(
            '/questionnaires/tests/files/xls-form-attrs.xlsx', 'rb')
        form = self.storage.save('xls-forms/xls-form-attrs.xlsx', file.read())
        file.close()
        self.project = ProjectFactory.create()
        Questionnaire.objects.create_from_form(
            xls_form=form,
            project=self.project
        )
        # test for expected schema and attribute creation
        assert 6 == Schema.objects.all().count()
        assert 10 == Attribute.objects.all().count()

    def test_get_attributes(self):
        mixin = SchemaSelectorMixin()
        project_attrs = mixin.get_attributes(self.project)

        # spatial unit attributes
        spatial_unit_attrs = project_attrs.get('spatial.spatialunit', [])
        assert 'DEFAULT' in spatial_unit_attrs.keys()
        su_defaults = spatial_unit_attrs.get('DEFAULT', [])
        assert len(su_defaults) == 1
        su_attr = su_defaults.get('quality')
        assert su_attr.name == 'quality'

        # party relationship attributes
        party_rel_attrs = project_attrs.get('party.partyrelationship', [])
        assert len(party_rel_attrs) == 1
        party_rel_defaults = party_rel_attrs.get('DEFAULT', [])
        party_rel_attr = party_rel_defaults.get('notes')
        assert party_rel_attr.name == 'notes'

        # individual party attributes
        party_attrs = project_attrs.get('party.party', [])
        individual_party_attrs = party_attrs.get('IN', [])
        assert len(individual_party_attrs) == 4
        in_party_attr = individual_party_attrs.get('gender')
        assert in_party_attr.name == 'gender'

        # group party attributes
        party_attrs = project_attrs.get('party.party', [])
        group_party_attrs = party_attrs.get('GR', [])
        assert len(group_party_attrs) == 3
        gr_party_attr = group_party_attrs.get('number_of_members')
        assert gr_party_attr.name == 'number_of_members'

        # tenure relationship attributes
        tenure_attrs = project_attrs.get('party.tenurerelationship', [])
        tenure_defaults = tenure_attrs.get('DEFAULT', [])
        tenure_attr = tenure_defaults.get('notes')
        assert tenure_attr.name == 'notes'

    def test_get_model_attributes(self):
        mixin = SchemaSelectorMixin()
        party_attrs = mixin.get_model_attributes(
            self.project, 'party.party')
        assert len(party_attrs) == 3

        individual_party_attrs = party_attrs.get('IN', [])
        assert len(individual_party_attrs) == 4
        in_party_attr = individual_party_attrs.get('gender')
        assert in_party_attr.name == 'gender'
