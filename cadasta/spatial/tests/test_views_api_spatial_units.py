from django.utils.translation import gettext as _
from rest_framework import status as status_code

from organization.tests.factories import (ProjectFactory,
                                          OrganizationFactory)
from .factories import SpatialUnitFactory
from .base_classes import (RecordListBaseTestCase,
                           RecordCreateBaseTestCase,
                           RecordListAPITest,
                           RecordCreateAPITest,
                           RecordDetailBaseTestCase,
                           RecordDetailAPITest,
                           RecordUpdateAPITest,
                           RecordDeleteAPITest)
from ..models import SpatialUnit
from ..views import api


class SpatialUnitListTestCase(RecordListBaseTestCase,
                              RecordCreateBaseTestCase):

    record_model = SpatialUnit

    def setUp(self):
        super().setUp()
        self.view = api.SpatialUnitList.as_view()
        self.url = '/v1/organizations/{org}/projects/{prj}/spatial/'

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        SpatialUnitFactory.create(project=prj, type='AP')
        SpatialUnitFactory.create(project=prj, type='BU')
        SpatialUnitFactory.create(
            project=prj, type='RW')
        self.num_records = 3
        return (org, prj)


class SpatialUnitListAPITest(SpatialUnitListTestCase,
                             RecordListAPITest):

    def test_full_list(self):
        org, prj = self._test_objs()
        extra_record = SpatialUnitFactory.create()
        content = self._get(
            org_slug=org.slug, prj_slug=prj.slug,
            status=status_code.HTTP_200_OK, length=self.num_records)
        assert extra_record.id not in (
            [u['properties']['id'] for u in content['features']])

    # def test_search_filter(self):
    #     org, prj = self._test_objs()
    #     content = self._get(
    #         org_slug=org.slug, prj_slug=prj.slug,
    #         status=status_code.HTTP_200_OK, length=1, query='search=AP')
    #     assert all(
    #         record['properties']['type'] == 'AP' for
    #         record in content['features'])

    def test_ordering(self):
        org, prj = self._test_objs()
        content = self._get(
            org_slug=org.slug, prj_slug=prj.slug,
            status=status_code.HTTP_200_OK, length=self.num_records,
            query='ordering=type')
        names = [
            record['properties']['type'] for record in content['features']]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        org, prj = self._test_objs()
        content = self._get(
            org_slug=org.slug, prj_slug=prj.slug,
            status=status_code.HTTP_200_OK, length=self.num_records,
            query='ordering=-type')
        names = [
            record['properties']['type'] for record in content['features']]
        assert names == sorted(names, reverse=True)

    def test_type_filter(self):
        org, prj = self._test_objs()
        content = self._get(
            org_slug=org.slug, prj_slug=prj.slug,
            status=status_code.HTTP_200_OK, length=1, query='type=RW')
        assert all(
            record['properties']['type'] == 'RW' for
            record in content['features'])


class SpatialUnitCreateAPITest(SpatialUnitListTestCase,
                               RecordCreateAPITest):

    default_create_data = {
        'properties': {
            'type': "AP"
        },
        'geometry': {
            'type': 'Point',
            'coordinates': [100, 0]
        }
    }

    # Additional tests

    def test_create_invalid_spatial_unit(self):
        org, prj = self._test_objs()
        invalid_data = {
            'type': '',
            'geometry': {
                'type': 'Point',
                'coordinates': [100, 0]
            }
        }
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=invalid_data, status=status_code.HTTP_400_BAD_REQUEST)
        assert content['type'][0] == _('"" is not a valid choice.')

    def test_create_spatial_unit_with_invalid_geometry(self):
        org, prj = self._test_objs()
        invalid_data = {
            'type': "BU",
            'geometry': {
                'type': 'Cats',
                'coordinates': [100, 0]
            }
        }
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=invalid_data, status=status_code.HTTP_400_BAD_REQUEST)
        assert content['geometry'][0] == _(
            "Invalid format: string or unicode input"
            " unrecognized as GeoJSON, WKT EWKT or HEXEWKB.")


class SpatialUnitDetailTestCase(RecordDetailBaseTestCase):

    model_name = 'SpatialUnit'
    record_factory = SpatialUnitFactory
    record_id_url_var_name = 'spatial_id'

    def setUp(self):
        super().setUp()
        self.view = api.SpatialUnitDetail.as_view()
        self.url = '/v1/organizations/{org}/projects/{prj}/spatial/{record}/'

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        su = SpatialUnitFactory.create(project=prj, type='AP')
        self.su = su
        return (su, org)


class SpatialUnitDetailAPITest(SpatialUnitDetailTestCase,
                               RecordDetailAPITest):

    def is_id_in_content(self, content, record_id):
        return content['properties']['id'] == record_id


class SpatialUnitUpdateAPITest(SpatialUnitDetailTestCase,
                               RecordUpdateAPITest):

    def get_valid_updated_data(self):
        return {'type': "BU"}

    def check_for_updated(self, content):
        data = self.get_valid_updated_data()
        assert content['properties']['type'] == data['type']

    def check_for_unchanged(self, content):
        assert content['properties']['type'] == self.su.type

    # Additional tests

    def test_update_with_invalid_data(self):

        def get_invalid_data(): return {'type': ''}

        content = self._test_patch_public_record(
            get_invalid_data, status_code.HTTP_400_BAD_REQUEST)
        assert content['type'][0] == _('"" is not a valid choice.')

    def test_update_with_invalid_geometry(self):

        def get_invalid_data():
            return {
                'geometry': {
                    'type': 'Cats',
                    'coordinates': [100, 0]
                }
            }

        content = self._test_patch_public_record(
            get_invalid_data, status_code.HTTP_400_BAD_REQUEST)
        assert content['geometry'][0] == _(
            "Invalid format: string or unicode input"
            " unrecognized as GeoJSON, WKT EWKT or HEXEWKB.")


class SpatialUnitDeleteAPITest(SpatialUnitDetailTestCase,
                               RecordDeleteAPITest):
    pass
