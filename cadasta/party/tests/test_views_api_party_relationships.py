from django.utils.translation import ugettext as _
from rest_framework import status as status_code

from organization.tests.factories import (ProjectFactory,
                                          OrganizationFactory)
from party.tests.factories import (PartyFactory,
                                   PartyRelationshipFactory)
from spatial.tests.base_classes import (RecordCreateBaseTestCase,
                                        RecordCreateAPITest,
                                        RecordDetailBaseTestCase,
                                        RecordDetailAPITest,
                                        RecordUpdateAPITest,
                                        RecordDeleteAPITest)
from party.models import PartyRelationship
from party.views import api


class PartyRelationshipCreateTestCase(RecordCreateBaseTestCase):

    record_model = PartyRelationship

    def setUp(self):
        super().setUp()
        self.view = api.PartyRelationshipCreate.as_view()
        self.url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'relationships/party/'
        )

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        party1 = PartyFactory.create(project=prj, name='Landowner')
        party2 = PartyFactory.create(project=prj, name='Leaser')
        party3 = PartyFactory.create(project=prj, name='Family')
        PR = PartyRelationshipFactory
        PR.create(project=prj, party1=party1, party2=party2)
        PR.create(project=prj, party1=party2, party2=party3)
        PR.create(project=prj, party1=party1, party2=party3)
        self.party1 = party1
        self.party2 = party2
        self.party3 = party3
        self.num_records = 3
        return (org, prj)


class PartyRelationshipCreateAPITest(PartyRelationshipCreateTestCase,
                                     RecordCreateAPITest):

    @property
    def default_create_data(self):
        return {
            'party1': self.party2.id,
            'party2': self.party1.id,
            'type': 'C'
        }

    # Additional tests

    def test_create_invalid_record_with_dupe_su(self):
        org, prj = self._test_objs()
        invalid_data = {
            'party1': self.party2.id,
            'party2': self.party2.id,
            'type': 'C'
        }
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=invalid_data, status=status_code.HTTP_400_BAD_REQUEST)
        assert content['non_field_errors'][0] == _(
            "The parties must be different")

    def test_create_invalid_record_with_different_project(self):
        org, prj = self._test_objs()
        other_prj = ProjectFactory.create(slug='other', organization=org)
        other_party = PartyFactory.create(project=other_prj, name="Other")
        invalid_data = {
            'party1': self.party1.id,
            'party2': other_party.id,
            'type': 'C'
        }
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=invalid_data, status=status_code.HTTP_400_BAD_REQUEST)
        err_msg = _(
            "'party1' project ({}) should be equal to 'party2' project ({})")
        assert content['non_field_errors'][0] == (
            err_msg.format(prj.slug, other_prj.slug))


class PartyRelationshipDetailTestCase(RecordDetailBaseTestCase):

    model_name = 'PartyRelationship'
    record_factory = PartyRelationshipFactory
    record_id_url_var_name = 'party_rel_id'

    def setUp(self):
        super().setUp()
        self.view = api.PartyRelationshipDetail.as_view()
        self.url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'relationships/party/{record}/'
        )

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        party1 = PartyFactory.create(project=prj, name='Landowner')
        party2 = PartyFactory.create(project=prj, name='Leaser')
        party3 = PartyFactory.create(project=prj, name='Family')
        rel = PartyRelationshipFactory.create(
            project=prj, party1=party1, party2=party2)
        self.party1 = party1
        self.party2 = party2
        self.party3 = party3
        return (rel, org)


class PartyRelationshipDetailAPITest(PartyRelationshipDetailTestCase,
                                     RecordDetailAPITest):

    def is_id_in_content(self, content, record_id):
        return content['id'] == record_id


class PartyRelationshipUpdateAPITest(PartyRelationshipDetailTestCase,
                                     RecordUpdateAPITest):

    def get_valid_updated_data(self):
        return {
            'party1': self.party3.id,
            'party2': self.party1.id,
        }

    def check_for_updated(self, content):
        assert content['party1'] == self.party3.id
        assert content['party2'] == self.party1.id

    def check_for_unchanged(self, content):
        assert content['party1']['name'] == "Landowner"
        assert content['party2']['name'] == "Leaser"

    # Additional tests

    def test_update_invalid_record_with_dupe_parties(self):

        def get_invalid_data():
            return {'party2': self.party1.id}

        content = self._test_patch_public_record(
            get_invalid_data, status_code.HTTP_400_BAD_REQUEST)
        assert content['non_field_errors'][0] == _(
            "The parties must be different")

    def test_update_invalid_record_with_different_project(self):

        other_org = OrganizationFactory.create(slug='other')
        other_prj = ProjectFactory.create(slug='other', organization=other_org)
        other_party = PartyFactory.create(project=other_prj, name="Other")

        def get_invalid_data():
            return {'party2': other_party.id}

        content = self._test_patch_public_record(
            get_invalid_data, status_code.HTTP_400_BAD_REQUEST)
        err_msg = _(
            "'party1' project ({}) should be equal to 'party2' project ({})")
        assert content['non_field_errors'][0] == (
            err_msg.format(self.party1.project.slug, other_prj.slug))


class PartyRelationshipDeleteAPITest(PartyRelationshipDetailTestCase,
                                     RecordDeleteAPITest):
    pass
