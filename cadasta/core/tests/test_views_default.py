import json

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from django.http import HttpRequest
from django.test import TestCase
from django.utils.encoding import force_text
from organization.models import OrganizationRole, Project
from organization.serializers import ProjectGeometrySerializer
from organization.tests.factories import OrganizationFactory, ProjectFactory
from skivvy import ViewTestCase
from tutelary.models import Role

from ..views.default import Dashboard, IndexPage, server_error
from config.settings.default import LEAFLET_CONFIG


class IndexPageTest(ViewTestCase, UserTestCase, TestCase):
    view_class = IndexPage

    def test_redirects_when_user_is_signed_in(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 302
        assert '/dashboard/' in response.location

    def test_page_is_rendered_when_user_is_not_signed_in(self):
        response = self.request()
        assert response.status_code == 302
        assert '/dashboard/' in response.location


class DashboardTest(ViewTestCase, UserTestCase, TestCase):
    view_class = Dashboard
    template = 'core/dashboard.html'

    def setup_models(self):
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
        ProjectFactory.create(
            name='Archived Project', archived=True,
            organization=self.org, extent=extent)

    def setup_template_context(self):
        context = {}
        context['leaflet_tiles'] = [
            {
                'label': force_text(label),
                'url': url,
                'attrs': force_text(attrs)
            } for (label, url, attrs) in LEAFLET_CONFIG.get('TILES')]
        return context

    def _render_geojson(self, projects):
        return json.dumps(ProjectGeometrySerializer(projects, many=True).data)

    def test_page_is_rendered_when_user_is_not_signed_in(self):
        response = self.request()
        assert response.status_code == 200

    def test_page_is_rendered_when_user_is_signed_in(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 200

    def test_private_projects_rendered_when_org_member_is_signed_in(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org, user=user)
        response = self.request(user=user)

        gj = self._render_geojson(Project.objects.filter(archived=False))
        expected_content = self.render_content(is_superuser=False, geojson=gj)
        assert response.status_code == 200
        assert response.content == expected_content

    def test_private_projects_not_rendered_when_not_an_org_member(self):
        user = UserFactory.create()
        response = self.request(user=user)

        gj = self._render_geojson(Project.objects.filter(access='public',
                                                         archived=False))
        expected_content = self.render_content(is_superuser=False, geojson=gj)
        assert response.status_code == 200
        assert response.content == expected_content

    def test_get_with_superuser(self):
        superuser = UserFactory.create()
        self.superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(self.superuser_role)
        response = self.request(user=superuser)

        gj = self._render_geojson(Project.objects.all())
        expected_content = self.render_content(is_superuser=True, geojson=gj)
        assert response.content == expected_content
        assert response.status_code == 200


class ServerErrorTest(TestCase):

    def setUp(self):
        super().setUp()
        self.request = HttpRequest()

    def test_server_error(self):
        response = server_error(self.request, template_name='500.html')
        assert response.status_code == 500
