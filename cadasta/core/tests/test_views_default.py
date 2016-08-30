import json

from accounts.tests.factories import UserFactory
from core.tests.base_test_case import UserTestCase
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.template import RequestContext
from django.template.loader import render_to_string
from django.test import TestCase
from organization.models import OrganizationRole, Project
from organization.serializers import ProjectGeometrySerializer
from organization.tests.factories import OrganizationFactory, ProjectFactory
from tutelary.models import Role

from ..views.default import Dashboard, IndexPage, server_error


class IndexPageTest(UserTestCase):

    def setUp(self):
        super().setUp()
        self.view = IndexPage.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

    def test_redirects_when_user_is_signed_in(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        assert response.status_code == 302
        assert '/dashboard/' in response['location']

    def test_page_is_rendered_when_user_is_not_signed_in(self):
        response = self.view(self.request)
        assert response.status_code == 302
        assert '/dashboard/' in response['location']


class DashboardTest(UserTestCase):

    def setUp(self):
        super().setUp()
        self.view = Dashboard.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        self.org = OrganizationFactory.create()
        extent = ('SRID=4326;'
                  'POLYGON ((-5.1031494140625000 8.1299292850467957, '
                  '-5.0482177734375000 7.6837733211111425, '
                  '-4.6746826171875000 7.8252894725496338, '
                  '-4.8641967773437491 8.2278005261522775, '
                  '-5.1031494140625000 8.1299292850467957))')
        ProjectFactory.create(organization=self.org, extent=extent)
        ProjectFactory.create(organization=self.org, extent=extent)
        ProjectFactory.create(
            name='Private Project',
            access='private', organization=self.org, extent=extent)

        setattr(self.request, 'user', AnonymousUser())

    def _test_projects_rendered(self, response, member=False, superuser=False):
        content = response.render().content.decode('utf-8')

        context = RequestContext(self.request)
        projects = []
        if superuser:
            projects = Project.objects.filter(extent__isnull=False)
        else:
            if member:
                projects.extend(Project.objects.filter(
                    organization__slug=self.org.slug,
                    access='private',
                    extent__isnull=False))
            projects.extend(Project.objects.filter(
                            access='public',
                            extent__isnull=False))
        context['geojson'] = json.dumps(
            ProjectGeometrySerializer(projects, many=True).data
        )
        context['is_superuser'] = superuser
        expected = render_to_string(
            'core/dashboard.html',
            context
        )

        assert expected == content

    def test_page_is_rendered_when_user_is_not_signed_in(self):
        response = self.view(self.request)
        assert response.status_code == 200

    def test_page_is_rendered_when_user_is_signed_in(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        assert response.status_code == 200

    def test_private_projects_rendered_when_org_member_is_signed_in(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org, user=user)
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        assert response.status_code == 200
        self._test_projects_rendered(response, member=True)

    def test_private_projects_not_rendered_when_not_an_org_member(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        assert response.status_code == 200
        self._test_projects_rendered(response)

    def test_get_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)
        setattr(self.request, 'user', superuser)
        response = self.view(self.request).render()
        assert response.status_code == 200
        self._test_projects_rendered(response, superuser=True)


class ServerErrorTest(TestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()

    def test_server_error(self):
        response = server_error(self.request, template_name='500.html')
        assert response.status_code == 500
