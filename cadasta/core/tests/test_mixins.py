from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse
from django.test import TestCase

from tutelary.models import assign_user_policies

from organization.views import default as org_views
from organization.tests.factories import ProjectFactory, OrganizationFactory
from spatial.views.default import LocationsAdd
from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase


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
