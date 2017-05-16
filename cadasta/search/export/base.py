import json
from collections import OrderedDict

from django.contrib.contenttypes.models import ContentType

from core.mixins import SchemaSelectorMixin
from party.models import TENURE_RELATIONSHIP_TYPES
from core.form_mixins import get_types
from .utils import convert_postgis_ewkb_to_ewkt


class Exporter(SchemaSelectorMixin):

    def __init__(self, project):
        self.project = project
        tenure_types = get_types(
            'tenure_type',
            TENURE_RELATIONSHIP_TYPES,
            questionnaire_id=project.current_questionnaire,
            include_labels=True)
        self.tenure_type_choices = dict(tenure_types)

        schema_attrs = self.get_attributes(self.project)

        get_content_type = ContentType.objects.get
        self.metadata = {
            'location': {
                'title': 'locations',
                'model_name': 'SpatialUnit',
                'content_type': get_content_type(app_label='spatial',
                                                 model='spatialunit'),
                'schema_attrs': schema_attrs['spatial.spatialunit'],
                'model_attrs': ['id', 'geometry.ewkt', 'type'],
            },
            'party': {
                'title': 'parties',
                'model_name': 'Party',
                'content_type': get_content_type(app_label='party',
                                                 model='party'),
                'schema_attrs': schema_attrs['party.party'],
                'model_attrs': ['id', 'name', 'type'],
            },
            'tenure_rel': {
                'title': 'relationships',
                'model_name': 'TenureRelationship',
                'content_type': get_content_type(app_label='party',
                                                 model='tenurerelationship'),
                'schema_attrs': schema_attrs['party.tenurerelationship'],
                'model_attrs': ['id', 'party_id', 'spatial_unit_id',
                                'tenure_type_id'],
            },
        }

        # Create ordered dict of all attributes, conditional or not
        for metadatum in self.metadata.values():
            attr_columns = OrderedDict(
                (a, '') for a in metadatum['model_attrs'])
            schema_columns = OrderedDict(
                (a.name, '')
                for attrs in metadatum['schema_attrs'].values()
                for a in attrs.values())
            attr_columns.update(schema_columns)
            metadatum['attr_columns'] = attr_columns

    def get_attr_values(self, item, metadatum):
        attr_values = {}
        for attr in metadatum['model_attrs']:
            attr_values[attr] = item[attr]

        conditional_selector = self.get_conditional_selector(
            metadatum['content_type'])
        if conditional_selector:
            entity_type = item[conditional_selector]
            attributes = metadatum['schema_attrs'].get(entity_type, {})
        else:
            attributes = metadatum['schema_attrs'].get('DEFAULT', {})
        for attr, _ in attributes.items():
            attr_value = item['attributes'].get(attr, '')
            if type(attr_value) == list:
                attr_value = ', '.join(attr_value)
            attr_values[attr] = attr_value

        return attr_values

    def process_entity(self, es_type_line, es_source_line, write_callback):
        # Extract ES type and source and skip if not loc/party/rel
        es_type = json.loads(es_type_line)['index']['_type']
        if es_type not in ('spatial', 'party'):
            return
        source = json.loads(es_source_line)

        # Get corresponding metadatum
        if es_type == 'spatial':
            metadatum = self.metadata['location']
        else:
            if source['tenure_id']:
                metadatum = self.metadata['tenure_rel']
            else:
                metadatum = self.metadata['party']

        # Reformat data to match model_attrs
        source['attributes'] = json.loads(source['attributes']['value'])
        if metadatum['model_name'] == 'SpatialUnit':
            if source['geometry'] is None:
                ewkt = ''
                wkt = ''
            else:
                ewkt = convert_postgis_ewkb_to_ewkt(
                    source['geometry']['value'])
                wkt = ewkt[10:]  # Remove SRID
            source['geometry.ewkt'] = ewkt
            source['geometry.wkt'] = wkt
        elif metadatum['model_name'] == 'TenureRelationship':
            source['id'] = source['tenure_id']
            source['party_id'] = source['tenure_partyid']
            source['tenure_type_id'] = source['tenure_type']
            source['tenure_type_label'] = str(
                self.tenure_type_choices[source['tenure_type']])
            source['attributes'] = json.loads(
                source['tenure_attributes']['value'])

        # Call callback
        write_callback(source, metadatum)
