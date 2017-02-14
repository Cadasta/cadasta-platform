import json

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from skivvy import ViewTestCase, APITestCase

from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from party.tests.factories import PartyFactory, TenureRelationshipFactory
from resources.tests.factories import ResourceFactory
from questionnaires.managers import create_attrs_schema
from questionnaires.tests import attr_schemas
from questionnaires.tests.factories import QuestionnaireFactory
from .. import views


class TransformTest(UserTestCase, TestCase):

    def setup_data(self):
        self.project = ProjectFactory.create()
        QuestionnaireFactory.create(project=self.project)

        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        create_attrs_schema(
            project=self.project,
            dict=attr_schemas.location_xform_group,
            content_type=content_type,
        )
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        create_attrs_schema(
            project=self.project,
            dict=attr_schemas.default_party_xform_group,
            content_type=content_type,
        )
        create_attrs_schema(
            project=self.project,
            dict=attr_schemas.individual_party_xform_group,
            content_type=content_type,
        )
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        create_attrs_schema(
            project=self.project,
            dict=attr_schemas.tenure_relationship_xform_group,
            content_type=content_type,
        )

        self.location = SpatialUnitFactory.create(
            project=self.project,
            geometry='SRID=4326;POINT(1 1)',
            attributes={
                'quality': 'point',
                'infrastructure': 'food',
            },
        )
        self.party = PartyFactory.create(
            project=self.project,
            type='IN',
            attributes={
                'gender': 'm',
                'homeowner': 'yes',
                'dob': '1951-05-05'
            },
        )
        self.tenure_rel = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit=self.location,
            party=self.party,
            attributes={'notes': 'The best relationship!'},
        )
        self.resource = ResourceFactory.create(project=self.project)

        self.location_raw_result = {
            'id': self.location.id,
            'type': self.location.type,
            'geometry': {
                'type': 'geometry',
                'value': '0101000020E6100000000000000000F03F000000000000F03F',
            },
            'attributes': {
                'type': 'jsonb',
                'value': '{"infrastructure": "food", "quality": "point"}',
            },
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }
        self.party_raw_result = {
            'id': self.party.id,
            'name': self.party.name,
            'type': 'IN',
            'attributes': {
                'type': 'jsonb',
                'value': ('{"dob": "1951-05-05",'
                          ' "gender": "m",'
                          ' "homeowner": "yes"}'),
            },
            'tenure_id': None,
            'tenure_attributes': None,
            'tenure_partyid': None,
            'spatial_unit_id': None,
            'tenure_type_id': None,
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }
        self.tenure_rel_raw_result = {
            'id': self.party.id,
            'name': self.party.name,
            'type': 'IN',
            'attributes': {
                'type': 'jsonb',
                'value': ('{"dob": "1951-05-05",'
                          ' "gender": "m",'
                          ' "homeowner": "yes"}'),
            },
            'tenure_id': self.tenure_rel.id,
            'tenure_attributes': {
                'type': 'jsonb',
                'value': '{"notes": "The best relationship!"}',
            },
            'tenure_partyid': self.party.id,
            'spatial_unit_id': self.location.id,
            'tenure_type_id': self.tenure_rel.tenure_type.id,
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }
        self.resource_raw_result = {
            'id': self.resource.id,
            'name': self.resource.name,
            'description': self.resource.description,
            'file': 'http://localhost:8000' + self.resource.file.url,
            'original_file': self.resource.original_file,
            'mime_type': self.resource.mime_type,
            'archived': self.resource.archived,
            'last_updated': self.resource.last_updated.isoformat(),
            'contributor_id': self.resource.contributor.id,
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }

    def test_transform_location_not_bulk(self):
        self.setup_data()
        result = views.transform(self.location)
        assert result == {
            '_type': 'spatial',
            '_source': self.location_raw_result,
        }

    def test_transform_location_bulk(self):
        self.setup_data()
        result = views.transform(self.location, bulk=True)
        assert result == [
            {'index': {'_type': 'spatial'}},
            self.location_raw_result,
        ]

    def test_transform_party_not_bulk(self):
        self.setup_data()
        result = views.transform(self.party)
        assert result == {
            '_type': 'party',
            '_source': self.party_raw_result,
        }

    def test_transform_party_bulk(self):
        self.setup_data()
        result = views.transform(self.party, bulk=True)
        assert result == [
            {'index': {'_type': 'party'}},
            self.party_raw_result,
        ]

    def test_transform_tenure_rel_not_bulk(self):
        self.setup_data()
        result = views.transform(self.tenure_rel)
        assert result == {
            '_type': 'party',
            '_source': self.tenure_rel_raw_result,
        }

    def test_transform_tenure_rel_bulk(self):
        self.setup_data()
        result = views.transform(self.tenure_rel, bulk=True)
        assert result == [
            {'index': {'_type': 'party'}},
            self.tenure_rel_raw_result,
        ]

    def test_transform_resource_rel_not_bulk(self):
        self.setup_data()
        result = views.transform(self.resource)
        assert result == {
            '_type': 'resource',
            '_source': self.resource_raw_result,
        }

    def test_transform_resource_bulk(self):
        self.setup_data()
        result = views.transform(self.resource, bulk=True)
        assert result == [
            {'index': {'_type': 'resource'}},
            self.resource_raw_result,
        ]


class AllEsTypesTest(APITestCase, UserTestCase, TestCase):

    view_class = views.AllEsTypes
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
        self.location = SpatialUnitFactory.create(
            project=self.project,
            geometry='SRID=4326;POINT(0 0)',
        )
        self.party1 = PartyFactory.create(project=self.project)
        self.party2 = PartyFactory.create(project=self.project)
        self.tenure_rel = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit=self.location,
            party=self.party1,
        )
        self.resource = ResourceFactory.create(project=self.project)

    def setup_url_kwargs(self):
        return {'projectid': self.project.id}

    def test_post_with_results(self):
        response = self.request(method='POST')
        assert response.status_code == 200
        assert response.content['hits']['total'] == 5
        hits = response.content['hits']['hits']
        assert len(hits) == 5
        assert hits[0]['_type'] == 'spatial'
        assert hits[0]['_source']['id'] == self.location.id
        assert hits[1]['_type'] == 'party'
        assert hits[1]['_source']['id'] == self.party1.id
        assert hits[1]['_source']['tenure_id'] is None
        assert hits[2]['_type'] == 'party'
        assert hits[2]['_source']['id'] == self.party1.id
        assert hits[2]['_source']['tenure_id'] == self.tenure_rel.id
        assert hits[3]['_type'] == 'resource'
        assert hits[3]['_source']['id'] == self.resource.id
        assert hits[4]['_type'] == 'party'
        assert hits[4]['_source']['id'] == self.party2.id
        assert hits[4]['_source']['tenure_id'] is None

    def test_post_with_paging(self):
        response = self.request(method='POST', post_data={'from': 4})
        assert response.status_code == 200
        assert response.content['hits']['total'] == 5
        hits = response.content['hits']['hits']
        assert len(hits) == 1
        assert hits[0]['_type'] == 'party'
        assert hits[0]['_source']['id'] == self.party2.id
        assert hits[0]['_source']['tenure_id'] is None

    def test_post_with_paging_out_of_range(self):
        response = self.request(method='POST', post_data={'from': 6})
        assert response.status_code == 200
        assert response.content['hits']['total'] == 5
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

    def test_post_with_limited_query(self):
        response = self.request(
            method='POST',
            post_data={'query': {'simple_query_string': {'query': 'LIMITED'}}}
        )
        assert response.status_code == 200
        assert response.content['hits']['total'] == 4
        hits = response.content['hits']['hits']
        assert len(hits) == 4
        assert hits[0]['_type'] == 'spatial'
        assert hits[0]['_source']['id'] == self.location.id
        assert hits[1]['_type'] == 'party'
        assert hits[1]['_source']['id'] == self.party1.id
        assert hits[1]['_source']['tenure_id'] is None
        assert hits[2]['_type'] == 'party'
        assert hits[2]['_source']['id'] == self.party1.id
        assert hits[2]['_source']['tenure_id'] == self.tenure_rel.id
        assert hits[3]['_type'] == 'resource'
        assert hits[3]['_source']['id'] == self.resource.id


class DumpAllEsTypesTest(ViewTestCase, UserTestCase, TestCase):

    view_class = views.DumpAllEsTypes

    def setup_models(self):
        self.project = ProjectFactory.create(slug='test-project')
        self.location = SpatialUnitFactory.create(
            project=self.project,
            geometry='SRID=4326;POINT(0 0)',
        )
        self.party1 = PartyFactory.create(project=self.project)
        self.party2 = PartyFactory.create(project=self.project)
        self.tenure_rel = TenureRelationshipFactory.create(
            project=self.project,
            spatial_unit=self.location,
            party=self.party1,
        )
        self.resource = ResourceFactory.create(project=self.project)

        self.query_format = (
            '{{"query": {{"simple_query_string": {{"query": "{q}"}}}},'
            ' "from": {f}, "size": {s}}}'
        )

    def setup_url_kwargs(self):
        return {'projectid': self.project.id}

    def test_get_with_results(self):
        query = self.query_format.format(q='test', f='0', s='10')
        response = self.request(get_data={'source': query})
        assert response.status_code == 200
        assert response.headers['content-type'][1] == 'text/plain'
        content = [json.loads(line) for line in response.content.splitlines()]
        assert len(content) == 10
        assert content[0]['index']['_type'] == 'spatial'
        assert content[1]['id'] == self.location.id
        assert content[2]['index']['_type'] == 'party'
        assert content[3]['id'] == self.party1.id
        assert content[3]['tenure_id'] is None
        assert content[4]['index']['_type'] == 'party'
        assert content[5]['id'] == self.party1.id
        assert content[5]['tenure_id'] == self.tenure_rel.id
        assert content[6]['index']['_type'] == 'resource'
        assert content[7]['id'] == self.resource.id
        assert content[8]['index']['_type'] == 'party'
        assert content[9]['id'] == self.party2.id
        assert content[9]['tenure_id'] is None

    def test_get_with_paging(self):
        query = self.query_format.format(q='test', f='3', s='1')
        response = self.request(get_data={'source': query})
        assert response.status_code == 200
        assert response.headers['content-type'][1] == 'text/plain'
        content = [json.loads(line) for line in response.content.splitlines()]
        assert len(content) == 2
        assert content[0]['index']['_type'] == 'resource'
        assert content[1]['id'] == self.resource.id

    def test_post_with_paging_out_of_range(self):
        query = self.query_format.format(q='test', f='6', s='10')
        response = self.request(get_data={'source': query})
        assert response.status_code == 200
        assert response.headers['content-type'][1] == 'text/plain'
        assert response.content == ''

    def test_post_with_none_query(self):
        query = self.query_format.format(q='NONE', f='0', s='10')
        response = self.request(get_data={'source': query})
        assert response.status_code == 200
        assert response.headers['content-type'][1] == 'text/plain'
        assert response.content == ''

    def test_post_with_error_query(self):
        query = self.query_format.format(q='ERROR', f='0', s='10')
        response = self.request(get_data={'source': query})
        assert response.status_code != 200

    def test_get_with_limited_query(self):
        query = self.query_format.format(q='LIMITED', f='0', s='10')
        response = self.request(get_data={'source': query})
        assert response.status_code == 200
        assert response.headers['content-type'][1] == 'text/plain'
        content = [json.loads(line) for line in response.content.splitlines()]
        assert len(content) == 8
        assert content[0]['index']['_type'] == 'spatial'
        assert content[1]['id'] == self.location.id
        assert content[2]['index']['_type'] == 'party'
        assert content[3]['id'] == self.party1.id
        assert content[3]['tenure_id'] is None
        assert content[4]['index']['_type'] == 'party'
        assert content[5]['id'] == self.party1.id
        assert content[5]['tenure_id'] == self.tenure_rel.id
        assert content[6]['index']['_type'] == 'resource'
        assert content[7]['id'] == self.resource.id


class SingleEsTypeTest(APITestCase, TestCase):

    view_class = views.SingleEsType
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
