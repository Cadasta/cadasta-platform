from django.utils.translation import ugettext as _
from rest_framework import status as status_code

from organization.tests.factories import (ProjectFactory,
                                          OrganizationFactory)
from .factories import (SpatialUnitFactory,
                        SpatialRelationshipFactory)
from .base_classes import (RecordCreateBaseTestCase,
                           RecordCreateAPITest,
                           RecordDetailBaseTestCase,
                           RecordDetailAPITest,
                           RecordUpdateAPITest,
                           RecordDeleteAPITest)
from ..models import SpatialRelationship
from ..views import api


class SpatialRelationshipCreateTestCase(RecordCreateBaseTestCase):

    record_model = SpatialRelationship

    def setUp(self):
        super().setUp()
        self.view = api.SpatialRelationshipCreate.as_view()
        self.url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'relationships/spatial/'
        )

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        su1 = SpatialUnitFactory.create(project=prj, name="House")
        su2 = SpatialUnitFactory.create(project=prj, name="Parcel")
        su3 = SpatialUnitFactory.create(project=prj, name="Bungalow")
        SpatialRelationshipFactory.create(project=prj, su1=su1, su2=su2)
        SpatialRelationshipFactory.create(project=prj, su1=su2, su2=su3)
        SpatialRelationshipFactory.create(project=prj, su1=su1, su2=su3)
        self.su1 = su1
        self.su2 = su2
        self.su3 = su3
        self.num_records = 3
        return (org, prj)


class SpatialRelationshipCreateAPITest(SpatialRelationshipCreateTestCase,
                                       RecordCreateAPITest):

    @property
    def default_create_data(self):
        return {
            'su1': self.su2.id,
            'su2': self.su1.id,
            'type': 'C'
        }

    # Additional tests

    def test_create_invalid_record_with_dupe_su(self):
        org, prj = self._test_objs()
        invalid_data = {
            'su1': self.su2.id,
            'su2': self.su2.id,
            'type': 'C'
        }
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=invalid_data, status=status_code.HTTP_400_BAD_REQUEST)
        assert content['non_field_errors'][0] == _(
            "The spatial units must be different")

    def test_create_invalid_record_with_different_project(self):
        org, prj = self._test_objs()
        other_prj = ProjectFactory.create(slug='other', organization=org)
        other_su = SpatialUnitFactory.create(project=other_prj, name="Other")
        invalid_data = {
            'su1': self.su1.id,
            'su2': other_su.id,
            'type': 'C'
        }
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=invalid_data, status=status_code.HTTP_400_BAD_REQUEST)
        err_msg = _("'su1' project ({}) should be equal to 'su2' project ({})")
        assert content['non_field_errors'][0] == (
            err_msg.format(prj.slug, other_prj.slug))


class SpatialRelationshipDetailTestCase(RecordDetailBaseTestCase):

    model_name = 'SpatialRelationship'
    record_factory = SpatialRelationshipFactory
    record_id_url_var_name = 'spatial_rel_id'

    def setUp(self):
        super().setUp()
        self.view = api.SpatialRelationshipDetail.as_view()
        self.url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'relationships/spatial/{record}/'
        )

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        su1 = SpatialUnitFactory.create(project=prj, name="House")
        su2 = SpatialUnitFactory.create(project=prj, name="Parcel")
        su3 = SpatialUnitFactory.create(project=prj, name="Bungalow")
        rel = SpatialRelationshipFactory.create(
            project=prj, su1=su1, su2=su2)
        self.su1 = su1
        self.su2 = su2
        self.su3 = su3
        return (rel, org)


class SpatialRelationshipDetailAPITest(SpatialRelationshipDetailTestCase,
                                       RecordDetailAPITest):

    def is_id_in_content(self, content, record_id):
        return content['id'] == record_id


class SpatialRelationshipUpdateAPITest(SpatialRelationshipDetailTestCase,
                                       RecordUpdateAPITest):

    def get_valid_updated_data(self):
        return {
            'su1': self.su2.id,
            'su2': self.su3.id,
        }

    def check_for_updated(self, content):
        assert content['su1'] == self.su2.id
        assert content['su2'] == self.su3.id

    def check_for_unchanged(self, content):
        assert content['su1']['properties']['name'] == "House"
        assert content['su2']['properties']['name'] == "Parcel"

    # Additional tests

    def test_update_invalid_record_with_dupe_su(self):

        def get_invalid_data():
            return {'su2': self.su1.id}

        content = self._test_patch_public_record(
            get_invalid_data, status_code.HTTP_400_BAD_REQUEST)
        assert content['non_field_errors'][0] == _(
            "The spatial units must be different")

    def test_update_invalid_record_with_different_project(self):

        other_org = OrganizationFactory.create(slug='other')
        other_prj = ProjectFactory.create(slug='other', organization=other_org)
        other_su = SpatialUnitFactory.create(project=other_prj, name="Other")

        def get_invalid_data():
            return {'su2': other_su.id}

        content = self._test_patch_public_record(
            get_invalid_data, status_code.HTTP_400_BAD_REQUEST)
        err_msg = _("'su1' project ({}) should be equal to 'su2' project ({})")
        assert content['non_field_errors'][0] == (
            err_msg.format(self.su1.project.slug, other_prj.slug))


class SpatialRelationshipDeleteAPITest(SpatialRelationshipDetailTestCase,
                                       RecordDeleteAPITest):
    pass
