from django.utils.translation import ugettext as _
from rest_framework import status as status_code

from organization.tests.factories import (ProjectFactory,
                                          OrganizationFactory)
from spatial.tests.factories import SpatialUnitFactory
from party.tests.factories import (PartyFactory,
                                   TenureRelationshipFactory)
from spatial.tests.base_classes import (RecordCreateBaseTestCase,
                                        RecordCreateAPITest,
                                        RecordDetailBaseTestCase,
                                        RecordDetailAPITest,
                                        RecordUpdateAPITest,
                                        RecordDeleteAPITest)
from party.models import TenureRelationship
from party.views import api


class TenureRelationshipCreateTestCase(RecordCreateBaseTestCase):

    record_model = TenureRelationship

    def setUp(self):
        super().setUp()
        self.view = api.TenureRelationshipCreate.as_view()
        self.url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'relationships/tenure/'
        )

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        party1 = PartyFactory.create(project=prj, name='Landowner')
        party2 = PartyFactory.create(project=prj, name='Family')
        su1 = SpatialUnitFactory.create(project=prj, type='PA')
        su2 = SpatialUnitFactory.create(project=prj, type='PA')
        TR = TenureRelationshipFactory
        rel1 = TR.create(project=prj, party=party1, spatial_unit=su1)
        TR.create(project=prj, party=party1, spatial_unit=su2)
        TR.create(project=prj, party=party2, spatial_unit=su1)
        self.party1 = party1
        self.party2 = party2
        self.su2 = su2
        self.tenure_type = rel1.tenure_type
        self.num_records = 3
        return (org, prj)


class TenureRelationshipCreateAPITest(TenureRelationshipCreateTestCase,
                                      RecordCreateAPITest):

    @property
    def default_create_data(self):
        return {
            'party': self.party2.id,
            'spatial_unit': self.su2.id,
            'tenure_type': self.tenure_type.id
        }

    # Additional tests

    def test_create_invalid_record_with_different_project(self):
        org, prj = self._test_objs()
        other_prj = ProjectFactory.create(slug='other', organization=org)
        other_party = PartyFactory.create(project=other_prj, name="Other")
        invalid_data = {
            'party': other_party.id,
            'spatial_unit': self.su2.id,
            'tenure_type': self.tenure_type.id
        }
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=invalid_data, status=status_code.HTTP_400_BAD_REQUEST)
        err_msg = _(
            "'party' project ({}) should be equal to "
            "'spatial_unit' project ({})")
        assert content['non_field_errors'][0] == (
            err_msg.format(other_prj.slug, prj.slug))


class TenureRelationshipDetailTestCase(RecordDetailBaseTestCase):

    model_name = 'TenureRelationship'
    record_factory = TenureRelationshipFactory
    record_id_url_var_name = 'tenure_rel_id'

    def setUp(self):
        super().setUp()
        self.view = api.TenureRelationshipDetail.as_view()
        self.url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'relationships/tenure/{record}/'
        )

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        party = PartyFactory.create(project=prj, name='Landowner')
        party2 = PartyFactory.create(project=prj, name='Family')
        spatial_unit = SpatialUnitFactory.create(project=prj, type='PA')
        spatial_unit2 = SpatialUnitFactory.create(project=prj, type='PA')
        rel = TenureRelationshipFactory.create(
            project=prj, party=party, spatial_unit=spatial_unit)
        self.party2 = party2
        self.spatial_unit = spatial_unit
        self.spatial_unit2 = spatial_unit2
        return (rel, org)


class TenureRelationshipDetailAPITest(TenureRelationshipDetailTestCase,
                                      RecordDetailAPITest):

    def is_id_in_content(self, content, record_id):
        return content['id'] == record_id


class TenureRelationshipUpdateAPITest(TenureRelationshipDetailTestCase,
                                      RecordUpdateAPITest):

    def get_valid_updated_data(self):
        return {
            'party': self.party2.id,
            'spatial_unit': self.spatial_unit2.id,
        }

    def check_for_updated(self, content):
        assert content['party'] == self.party2.id
        assert content['spatial_unit'] == self.spatial_unit2.id

    def check_for_unchanged(self, content):
        assert content['party']['name'] == "Landowner"
        assert content['spatial_unit']['properties']['type'] == "PA"

    # Additional tests

    def test_update_invalid_record_with_different_project(self):

        other_org = OrganizationFactory.create(slug='other')
        other_prj = ProjectFactory.create(slug='other', organization=other_org)
        other_party = PartyFactory.create(project=other_prj, name="Other")

        def get_invalid_data():
            return {'party': other_party.id}

        content = self._test_patch_public_record(
            get_invalid_data, status_code.HTTP_400_BAD_REQUEST)
        err_msg = _(
            "'party' project ({}) should be equal to "
            "'spatial_unit' project ({})")
        assert content['non_field_errors'][0] == (
            err_msg.format(other_prj.slug, self.spatial_unit.project.slug))


class TenureRelationshipDeleteAPITest(TenureRelationshipDetailTestCase,
                                      RecordDeleteAPITest):
    pass
