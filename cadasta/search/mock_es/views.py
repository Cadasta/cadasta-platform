import json

from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from organization.models import Project
from spatial.models import SpatialUnit
from party.models import Party, TenureRelationship
from resources.models import Resource


def transform(entity, bulk=False):

    if type(entity) is SpatialUnit:
        source = {
            'id': entity.id,
            'type': entity.type,
            'geometry': {
                'type': 'geometry',
                'value': ''.join(
                    ['{:02X}'.format(x) for x in entity.geometry.ewkb]
                ),
            },
            'attributes': {
                'type': 'jsonb',
                'value': json.dumps(dict(entity.attributes), sort_keys=True),
            },
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }
        if bulk:
            return [{'index': {'_type': 'spatial'}}, source]
        else:
            return {'_type': 'spatial', '_source': source}

    if type(entity) is Party:
        source = {
            'id': entity.id,
            'name': entity.name,
            'type': entity.type,
            'attributes': {
                'type': 'jsonb',
                'value': json.dumps(dict(entity.attributes), sort_keys=True),
            },
            'tenure_id': None,
            'tenure_attributes': None,
            'tenure_partyid': None,
            'spatial_unit_id': None,
            'tenure_type_id': None,
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }
        if bulk:
            return [{'index': {'_type': 'party'}}, source]
        else:
            return {'_type': 'party', '_source': source}

    if type(entity) is TenureRelationship:
        source = {
            'id': entity.party.id,
            'name': entity.party.name,
            'type': entity.party.type,
            'attributes': {
                'type': 'jsonb',
                'value': json.dumps(dict(entity.party.attributes),
                                    sort_keys=True),
            },
            'tenure_id': entity.id,
            'tenure_attributes': {
                'type': 'jsonb',
                'value': json.dumps(dict(entity.attributes), sort_keys=True),
            },
            'tenure_partyid': entity.party.id,
            'spatial_unit_id': entity.spatial_unit.id,
            'tenure_type_id': entity.tenure_type.id,
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }
        if bulk:
            return [{'index': {'_type': 'party'}}, source]
        else:
            return {'_type': 'party', '_source': source}

    if type(entity) is Resource:
        source = {
            'id': entity.id,
            'name': entity.name,
            'description': entity.description,
            'file': 'http://localhost:8000' + entity.file.url,
            'original_file': entity.original_file,
            'mime_type': entity.mime_type,
            'archived': entity.archived,
            'last_updated': entity.last_updated.isoformat(),
            'contributor_id': entity.contributor.id,
            '@timestamp': '2017-01-01T01:23:45.678Z',
        }
        if bulk:
            return [{'index': {'_type': 'resource'}}, source]
        else:
            return {'_type': 'resource', '_source': source}


class BaseAllEsTypes(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    parser_classes = (JSONParser,)

    def search(self, query_dsl):

        query = query_dsl['query']['simple_query_string']['query'].lower()
        if query == 'error':
            return Response({}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        entities = []
        page = []
        if query != 'none':
            project = Project.objects.get(id=self.kwargs['projectid'])
            locations = list(SpatialUnit.objects.filter(project=project))
            parties = list(Party.objects.filter(project=project))
            rels = list(TenureRelationship.objects.filter(project=project))
            resources = list(Resource.objects.filter(project=project))

            while (
                len(locations) + len(parties) + len(rels) + len(resources) > 0
            ):
                if len(locations) > 0:
                    entities.append(locations.pop(0))
                if len(parties) > 0:
                    entities.append(parties.pop(0))
                if len(rels) > 0:
                    entities.append(rels.pop(0))
                if len(resources) > 0:
                    entities.append(resources.pop(0))
                if query == 'limited':
                    break

            start_idx = query_dsl.get('from', 0)
            end_idx = start_idx + query_dsl.get('size', 10)
            page = entities[start_idx:end_idx]

        if self.bulk:
            body = []
            for entity in page:
                body.extend(transform(entity, bulk=True))
            return HttpResponse(
                ''.join([json.dumps(line) + '\n' for line in body]),
                content_type="text/plain"
            )
        else:
            return Response({
                'hits': {
                    'total': len(entities),
                    'hits': [transform(entity) for entity in page],
                },
            })


class AllEsTypes(BaseAllEsTypes):

    def __init__(self):
        self.bulk = False

    def post(self, request, *args, **kwargs):
        return self.search(request.data)


class DumpAllEsTypes(BaseAllEsTypes):

    def __init__(self):
        self.bulk = True

    def get(self, request, *args, **kwargs):
        return self.search(json.loads(request.query_params['source']))


class SingleEsType(APIView):

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
