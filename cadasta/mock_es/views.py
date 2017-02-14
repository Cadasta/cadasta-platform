import json

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from organization.models import Project
from spatial.models import SpatialUnit
from party.models import Party, TenureRelationship
from resources.models import Resource


class EsAllTypes(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):
        # Handle no results and error overrides
        query = request.data['query']['simple_query_string']['query'].lower()
        if query == 'none':
            return Response({
                'hits': {
                    'total': 0,
                    'hits': [],
                },
            })
        if query == 'error':
            return Response({}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        project = Project.objects.get(id=self.kwargs['projectid'])
        locations = list(SpatialUnit.objects.filter(project=project))
        parties = list(Party.objects.filter(project=project))
        rels = list(TenureRelationship.objects.filter(project=project))
        resources = list(Resource.objects.filter(project=project))

        entities = []
        while len(locations) + len(parties) + len(rels) + len(resources) > 0:
            if len(locations) > 0:
                entities.append(locations.pop(0))
            if len(parties) > 0:
                entities.append(parties.pop(0))
            if len(rels) > 0:
                entities.append(rels.pop(0))
            if len(resources) > 0:
                entities.append(resources.pop(0))

        start_idx = request.data.get('from', 0)
        num_page_results = request.data.get('size', 10)

        hits = []
        for entity in entities[start_idx:start_idx + num_page_results]:
            hits.append(self.transform(entity))

        return Response({
            'hits': {
                'total': len(entities),
                'hits': hits,
            },
        })

    def transform(self, entity):
        if type(entity) is SpatialUnit:
            return {
                '_type': 'spatial',
                '_source': {
                    'id': entity.id,
                    'type': entity.type,
                    'attributes': {
                        'type': 'jsonb',
                        'value': json.dumps(dict(entity.attributes)),
                    },
                    '@timestamp': '2017-01-01T01:23:45.678Z',
                },
            }
        if type(entity) is Party:
            return {
                '_type': 'party',
                '_source': {
                    'id': entity.id,
                    'name': entity.name,
                    'type': entity.type,
                    'attributes': {
                        'type': 'jsonb',
                        'value': json.dumps(dict(entity.attributes)),
                    },
                    'tenure_id': None,
                    'tenure_attributes': None,
                    'tenure_partyid': None,
                    'spatial_unit_id': None,
                    'tenure_type_id': None,
                    '@timestamp': '2017-01-01T01:23:45.678Z',
                },
            }
        if type(entity) is TenureRelationship:
            return {
                '_type': 'party',
                '_source': {
                    'id': entity.party.id,
                    'name': entity.party.name,
                    'type': entity.party.type,
                    'attributes': {
                        'type': 'jsonb',
                        'value': json.dumps(dict(entity.party.attributes)),
                    },
                    'tenure_id': entity.id,
                    'tenure_attributes': {
                        'type': 'jsonb',
                        'value': json.dumps(dict(entity.attributes)),
                    },
                    'tenure_partyid': entity.party.id,
                    'spatial_unit_id': entity.spatial_unit.id,
                    'tenure_type_id': entity.tenure_type.id,
                    '@timestamp': '2017-01-01T01:23:45.678Z',
                },
            }
        if type(entity) is Resource:
            return {
                '_type': 'resource',
                '_source': {
                    'id': entity.id,
                    'name': entity.name,
                    'description': entity.description,
                    'file': entity.file.url,
                    'original_file': entity.original_file,
                    'mime_type': entity.mime_type,
                    'archived': entity.archived,
                    'last_updated': entity.last_updated,
                    'contributor_id': entity.contributor.id,
                    '@timestamp': '2017-01-01T01:23:45.678Z',
                },
            }


class EsSingleType(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        if self.kwargs['type'] == 'project':
            # Search for project type is only used for getting the timestamp
            return Response({
                'hits': {
                    'hits': [{
                        '_source': {'@timestamp': '2017-01-01T01:23:45.678Z'},
                    }],
                },
            })
        else:
            # TODO: No search by type yet
            return Response({})
