import pytest

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test import TestCase
from jsonattrs.models import Attribute, Schema
from organization.tests.factories import OrganizationFactory, ProjectFactory
from organization.views import default as org_views

from questionnaires.models import Questionnaire
from spatial.views.async import LocationsAdd
from tutelary.models import assign_user_policies

from ..mixins import SchemaSelectorMixin


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

    def test_login_redirect_from_project_dashboard_to_org_dashboard(self):
        user = UserFactory.create()
        assign_user_policies(user, *[])
        project = ProjectFactory.create()

        view = org_views.ProjectMap.as_view()

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
        assign_user_policies(user, *[])
        org = OrganizationFactory.create()
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
