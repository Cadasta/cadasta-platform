import json

from django.utils.translation import gettext as _
from rest_framework import status as status_code
from rest_framework.test import APIRequestFactory, force_authenticate

from organization.tests.factories import (ProjectFactory,
                                          OrganizationFactory)
from spatial.tests.factories import (SpatialUnitFactory,
                                     SpatialRelationshipFactory)
from party.tests.factories import (PartyFactory,
                                   PartyRelationshipFactory,
                                   TenureRelationshipFactory)
from spatial.tests.base_classes import RecordBaseTestCase
from party.views.api import RelationshipList


class RelationshipListTestCase(RecordBaseTestCase):

    def setUp(self):
        super().setUp()
        self.view = RelationshipList.as_view()

    def _test_objs(self, access='public'):
        org = OrganizationFactory.create(slug='namati')
        prj = ProjectFactory.create(
            slug='test-project', organization=org, access=access)
        su1 = SpatialUnitFactory.create(project=prj, name='Parcel')
        su2 = SpatialUnitFactory.create(project=prj, name='House')
        su3 = SpatialUnitFactory.create(project=prj, name='Village')
        self.su1 = su1
        self.su2 = su2
        self.su3 = su3
        party1 = PartyFactory.create(project=prj, name='Landowner')
        party2 = PartyFactory.create(project=prj, name='Family')
        party3 = PartyFactory.create(project=prj, name='Leasee')
        self.party1 = party1
        self.party2 = party2
        self.party3 = party3
        SR = SpatialRelationshipFactory
        PR = PartyRelationshipFactory
        TR = TenureRelationshipFactory
        self.sr1 = SR.create(project=prj, su1=su1, su2=su2)
        self.sr2 = SR.create(project=prj, su1=su1, su2=su3)
        self.sr3 = SR.create(project=prj, su1=su2, su2=su3)
        self.pr1 = PR.create(project=prj, party1=party1, party2=party2)
        self.pr2 = PR.create(project=prj, party1=party1, party2=party3)
        self.pr3 = PR.create(project=prj, party1=party2, party2=party3)
        self.tr1 = TR.create(project=prj, party=party1, spatial_unit=su2)
        self.tr2 = TR.create(project=prj, party=party1, spatial_unit=su3)
        self.tr3 = TR.create(project=prj, party=party2, spatial_unit=su3)
        return (org, prj)


class SpatialUnitsRelationshipListAPITest(RelationshipListTestCase):

    def test_get_all_relationships_of_spatial_unit(self):
        org, prj = self._test_objs()
        url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'spatial/{record}/relationships/'
        ).format(org=org.slug, prj=prj.slug, record=self.su1.id)
        request = APIRequestFactory().get(url)
        force_authenticate(request, user=self.user)
        response = self.view(
            request, organization=org.slug, project=prj.slug,
            spatial_id=self.su1.id).render()
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status_code.HTTP_200_OK
        assert len(content) == 2
        valid_ids = (self.sr1.id, self.sr2.id)
        for rel in content:
            assert rel['id'] in valid_ids

    def test_get_all_relationships_of_party(self):
        org, prj = self._test_objs()
        url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'party/{record}/relationships/'
        ).format(org=org.slug, prj=prj.slug, record=self.party1.id)
        request = APIRequestFactory().get(url)
        force_authenticate(request, user=self.user)
        response = self.view(
            request, organization=org.slug, project=prj.slug,
            party_id=self.party1.id).render()
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status_code.HTTP_200_OK
        assert len(content) == 4
        valid_ids = (self.pr1.id, self.pr2.id, self.tr1.id, self.tr2.id)
        for rel in content:
            assert rel['id'] in valid_ids

    def test_get_invalid_relationship_class(self):
        org, prj = self._test_objs()
        url = (
            '/v1/organizations/{org}/projects/{prj}/'
            'party/{record}/relationships/?class=nonsense'
        ).format(org=org.slug, prj=prj.slug, record=self.party1.id)
        request = APIRequestFactory().get(url)
        force_authenticate(request, user=self.user)
        response = self.view(
            request, organization=org.slug, project=prj.slug,
            party_id=self.party1.id).render()
        content = json.loads(response.content.decode('utf-8'))
        assert response.status_code == status_code.HTTP_400_BAD_REQUEST
        assert content['detail'] == _("Relationship class is unknown")
