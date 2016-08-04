import json

from django.test import TestCase
from tutelary.models import Policy
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from spatial.tests import factories as spatial_factories
from party.tests import factories as party_factories
from party.views.api import RelationshipList


class SpatialUnitsRelationshipListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = RelationshipList

    def setup_models(self):
        clauses = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['project/*/*',
                               'spatial/*/*/*',
                               'spatial_rel/*/*/*',
                               'party/*/*/*',
                               'party_rel/*/*/*',
                               'tenure_rel/*/*/*'],
                    'action': ['project.*',
                               'project.*.*',
                               'spatial.*',
                               'spatial_rel.*',
                               'party.*',
                               'party_rel.*',
                               'tenure_rel.*']
                }
            ]
        }
        policy = Policy.objects.create(
            name='basic-test',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.SR = spatial_factories.SpatialRelationshipFactory
        self.PR = party_factories.PartyRelationshipFactory
        self.TR = party_factories.TenureRelationshipFactory

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug
        }

    def test_get_all_relationships_of_spatial_unit(self):
        su1 = spatial_factories.SpatialUnitFactory.create(project=self.prj)
        su2 = spatial_factories.SpatialUnitFactory.create(project=self.prj)
        su3 = spatial_factories.SpatialUnitFactory.create(project=self.prj)
        sr1 = self.SR.create(project=self.prj, su1=su1, su2=su2)
        sr2 = self.SR.create(project=self.prj, su1=su1, su2=su3)
        self.SR.create(project=self.prj, su1=su2, su2=su3)
        self.TR.create(project=self.prj, spatial_unit=su2)

        response = self.request(user=self.user,
                                url_kwargs={'spatial_id': su1.id})
        assert response.status_code == 200
        assert len(response.content) == 2
        valid_ids = (sr1.id, sr2.id)
        for rel in response.content:
            assert rel['id'] in valid_ids

    def test_get_all_relationships_of_party(self):
        party1 = party_factories.PartyFactory.create(project=self.prj)
        party2 = party_factories.PartyFactory.create(project=self.prj)
        party3 = party_factories.PartyFactory.create(project=self.prj)
        su1 = spatial_factories.SpatialUnitFactory.create(project=self.prj)

        pr1 = self.PR.create(project=self.prj, party1=party1, party2=party2)
        pr2 = self.PR.create(project=self.prj, party1=party1, party2=party3)
        self.PR.create(project=self.prj, party1=party2, party2=party3)
        tr1 = self.TR.create(project=self.prj, party=party1, spatial_unit=su1)
        self.TR.create(project=self.prj, party=party2, spatial_unit=su1)

        response = self.request(user=self.user,
                                url_kwargs={'party_id': party1.id})
        assert response.status_code == 200
        assert len(response.content) == 3
        valid_ids = (pr1.id, pr2.id, tr1.id)
        for rel in response.content:
            assert rel['id'] in valid_ids

    def test_get_invalid_relationship_class(self):
        party = party_factories.PartyFactory.create(project=self.prj)
        response = self.request(user=self.user,
                                url_kwargs={'party_id': party.id},
                                get_data={'class': 'nonsense'})

        assert response.status_code == 400
        assert response.content['detail'] == "Relationship class is unknown"
