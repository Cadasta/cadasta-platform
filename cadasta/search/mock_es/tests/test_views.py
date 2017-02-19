from django.test import TestCase
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from party.tests.factories import PartyFactory, TenureRelationshipFactory
from resources.tests.factories import ResourceFactory
from .. import views


class AllTypesTest(APITestCase, UserTestCase, TestCase):

    view_class = views.EsAllTypes
    post_data = {
        'query': {
            'simple_query_string': {
                'query': 'test',
            },
        },
        'from': 0,
        'size': 10,
    }

    def setup_models(self):
        self.project = ProjectFactory.create(slug='test-project')
        self.su = SpatialUnitFactory.create(project=self.project)
        self.party = PartyFactory.create(project=self.project)
        self.tenure_rel = TenureRelationshipFactory.create(
            spatial_unit=self.su, party=self.party, project=self.project)
        self.resource = ResourceFactory.create(project=self.project)

    def setup_url_kwargs(self):
        return {'projectid': self.project.id}

    def test_post_with_results(self):
        response = self.request(method='POST')
        assert response.status_code == 200
        assert response.content['hits']['total'] == 4
        hits = response.content['hits']['hits']
        assert len(hits) == 4
        assert hits[0]['_type'] == 'spatial'
        assert hits[0]['_source']['id'] == self.su.id
        assert hits[1]['_type'] == 'party'
        assert hits[1]['_source']['id'] == self.party.id
        assert hits[1]['_source']['tenure_id'] is None
        assert hits[2]['_type'] == 'party'
        assert hits[2]['_source']['id'] == self.party.id
        assert hits[2]['_source']['tenure_id'] == self.tenure_rel.id
        assert hits[3]['_type'] == 'resource'
        assert hits[3]['_source']['id'] == self.resource.id

    def test_post_with_paging(self):
        response = self.request(method='POST', post_data={'from': 3})
        assert response.status_code == 200
        assert response.content['hits']['total'] == 4
        hits = response.content['hits']['hits']
        assert len(hits) == 1
        assert hits[0]['_type'] == 'resource'
        assert hits[0]['_source']['id'] == self.resource.id

    def test_post_with_paging_out_of_range(self):
        response = self.request(method='POST', post_data={'from': 5})
        assert response.status_code == 200
        assert response.content['hits']['total'] == 4
        assert response.content['hits']['hits'] == []

    def test_post_with_none_query(self):
        response = self.request(
            method='POST',
            post_data={'query': {'simple_query_string': {'query': 'NONE'}}}
        )
        assert response.status_code == 200
        assert response.content['hits']['total'] == 0
        assert response.content['hits']['hits'] == []

    def test_post_with_error_query(self):
        response = self.request(
            method='POST',
            post_data={'query': {'simple_query_string': {'query': 'ERROR'}}}
        )
        assert response.status_code != 200


class SingleTypeTest(APITestCase, TestCase):

    view_class = views.EsSingleType
    url_kwargs = {'projectid': 'foobar', 'type': 'project'}

    def test_get_with_project_type(self):
        response = self.request()
        assert response.status_code == 200
        hits = response.content['hits']['hits']
        assert len(hits) == 1
        assert hits[0]['_source']['@timestamp'] == '2017-01-01T01:23:45.678Z'

    def test_get_with_nonproject_type(self):
        response = self.request(url_kwargs={'type': 'foo'})
        assert response.status_code == 200
        assert response.content == {}
