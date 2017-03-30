import csv

from core.mixins import SchemaSelectorMixin
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from party.models import Party, TenureRelationship, TenureRelationshipType
from spatial.models import SpatialUnit

from . import exceptions, validators

ATTRIBUTE_GROUPS = settings.ATTRIBUTE_GROUPS

EXCLUDE_HEADERS = [
    'deviceid', 'sim_serial', 'start', 'end', 'today',
    'meta/instanceid', 'subscriberid', 'tenure_type'
]

CONTENT_TYPES = {
    'spatial.spatialunit': 'Location',
    'spatial.spatialrelationship': 'Spatial Relationship',
    'party.party': 'Party',
    'party.tenurerelationship': 'Tenure Relationship',
    'party.partyrelationship': 'Party Relationship'
}

ENTITY_TYPES = {
    'PT': 'party.party', 'SU': 'spatial.spatialunit',
    'TR': 'party.tenurerelationship'
}

XLS_WORKSHEET_TO_CONTENT_TYPE = {
    'spatial.spatialunit': 'locations',
    'party.party': 'parties',
    'party.tenurerelationship': 'relationships'
}


class Importer(SchemaSelectorMixin):

    class Meta:
        abstract = True

    def __init__(self, project, delimiter=',', quotechar='"'):
        self.project = project
        self.delimiter = delimiter
        self.quotechar = quotechar
        self._schema_attrs = {}
        self._parties_created = {}
        self._locations_created = {}

    def get_headers(self):
        raise NotImplementedError(
            "Your %s class has not defined a get_headers() method."
            % self.__class__.__name__
        )

    def import_data(self, config, **kwargs):
        raise NotImplementedError(
            "Your %s class has not defined an import_data() method."
            % self.__class__.__name__
        )

    def get_content_type_keys(self):
        content_type_keys = []
        for attribute_group in ATTRIBUTE_GROUPS:
            app_label = ATTRIBUTE_GROUPS[attribute_group]['app_label']
            model = ATTRIBUTE_GROUPS[attribute_group]['model']
            content_type_key = '{}.{}'.format(app_label, model)
            content_type_keys.append(content_type_key)
        return content_type_keys

    def get_schema_attrs(self):
        self._schema_attrs = self.get_attributes(self.project)
        return self._schema_attrs

    def get_attribute_map(self, type, entity_types, flatten=False):
        # make sure we pick up tenure attributes if
        # importing both parties and locations
        if 'PT' in entity_types and 'SU' in entity_types:
            entity_types.append('TR')

        attribute_map = {}
        extra_attrs, extra_headers, found_attrs = [], [], []
        selected_content_types = [
            ENTITY_TYPES[selection] for selection in entity_types
        ]

        project_attrs = self.get_schema_attrs()

        # build a dict of content_type to attrs selected for import
        selected_attrs = {
            content_type: attrs for content_type, attrs
            in project_attrs.items()
            if content_type in selected_content_types
        }

        # build list of attribute names not selected for import
        exclude_attrs = list(set([
            name.lower() for content_type, selectors
            in project_attrs.items()
            for selector, attrs in selectors.items()
            for name, attr in attrs.items()
            if content_type not in selected_content_types
        ]))

        for content_type, selectors in selected_attrs.items():
            attribute_map[content_type] = {}
            attr_map = {}
            for selector, attributes in selectors.items():
                attr_map[selector] = {}
                for attr_name, attr in attributes.items():
                    name = attr_name.lower()
                    if type == 'xls':
                        sheet = XLS_WORKSHEET_TO_CONTENT_TYPE.get(
                            content_type, None
                        )
                        headers = self.get_header_map().get(sheet, [])
                    else:
                        headers = self.get_headers()
                    if name in headers:
                        attr_map[selector][name] = (
                            attr, content_type, CONTENT_TYPES[content_type]
                        )
                        found_attrs.append(name)
                    else:
                        extra_attrs.append(name)
            attribute_map[content_type] = attr_map

        # enfoce uniqueness on these lists
        found_attrs = list(set(found_attrs))
        extra_attrs = list(set(extra_attrs))

        headers = self.get_headers()
        extra_headers = list(set([
            h for h in headers if h not in found_attrs and h not in
            exclude_attrs and h not in extra_attrs
        ]))

        if flatten:
            # return a simplified representation for use in import wizard
            flat_attr_map = {}
            for model, selectors in attribute_map.items():
                attr_list = {}
                for _, attributes in selectors.items():
                    attr_list.update({
                        attr_name: attrs for attr_name, attrs
                        in attributes.items()
                    })
                flat_attr_map[model.split('.')[1]] = attr_list
            return (flat_attr_map,
                    sorted(extra_attrs), sorted(extra_headers))

        return (attribute_map,
                sorted(extra_attrs), sorted(extra_headers))

    def _import(self, config, csvfile):
        attributes = config.get('attributes', None)
        entity_types = config.get('entity_types', None)
        type = config.get('type', None)
        (attr_map,
            extra_attrs, extra_headers) = self.get_attribute_map(
                type, entity_types)
        try:
            with transaction.atomic():
                reader = csv.reader(
                    csvfile, delimiter=self.delimiter,
                    quotechar=self.quotechar
                )
                headers = [h.lower() for h in next(reader)]

                for row in reader:
                    content_types = dict(
                        (key, None) for key in self.get_content_type_keys()
                    )
                    (party_name, party_type, geometry, location_type,
                        tenure_type) = validators.validate_row(
                            headers, row, config
                    )
                    if 'PT' in entity_types and party_type:
                        content_types['party.party'] = {
                            'project': self.project,
                            'name': party_name,
                            'type': party_type,
                            'attributes': {}
                        }
                    if 'SU' in entity_types and location_type:
                        content_types['spatial.spatialunit'] = {
                            'project': self.project,
                            'type': location_type,
                            'geometry': geometry,
                            'attributes': {}
                        }
                    if location_type and party_type and tenure_type:
                        content_types['party.tenurerelationship'] = {
                            'project': self.project,
                            'attributes': {}
                        }
                    content_types = self._map_attrs_to_content_types(
                        headers, row, content_types, attributes, attr_map)
                    self._create_models(
                        type, headers, row, content_types, tenure_type
                    )
        except ValidationError as e:
            raise exceptions.DataImportError(
                e.messages[0], line_num=reader.line_num)

    def _create_models(self, type, headers, row, content_types, tenure_type):

        party_ct = content_types['party.party']
        spatial_ct = content_types['spatial.spatialunit']

        s_id = (
            'tenurerelationship::spatial_unit_id'
            if type == 'xls' else 'spatial_unit_id')
        p_id = (
            'tenurerelationship::party_id'
            if type == 'xls' else 'party_id'
        )

        if spatial_ct:
            try:
                spatial_unit_id = row[headers.index(s_id)]
            except ValueError:
                su = SpatialUnit.objects.create(**spatial_ct)
            else:
                if spatial_unit_id:
                    created_su_id = self._locations_created.get(
                        spatial_unit_id, None
                    )
                    if created_su_id:
                        su = SpatialUnit.objects.get(id=created_su_id)
                    else:
                        su = SpatialUnit.objects.create(**spatial_ct)
                        self._locations_created[spatial_unit_id] = su.pk
                else:
                    su = SpatialUnit.objects.create(**spatial_ct)
                    self._locations_created[spatial_unit_id] = su.pk

        if party_ct:
            try:
                party_id = row[headers.index(p_id)]
            except ValueError:
                party = Party.objects.create(**party_ct)
            else:
                if party_id:
                    created_party_id = self._parties_created.get(
                        party_id, None)
                    if created_party_id:
                        party = Party.objects.get(id=created_party_id)
                    else:
                        party = Party.objects.create(**party_ct)
                        self._parties_created[party_id] = party.pk
                else:
                    party = Party.objects.create(**party_ct)
                    self._parties_created[party_id] = party.pk

        if party_ct and spatial_ct:
            tt = TenureRelationshipType.objects.get(id=tenure_type)
            content_types['party.tenurerelationship']['party'] = party
            content_types['party.tenurerelationship']['spatial_unit'] = su
            content_types['party.tenurerelationship']['tenure_type'] = tt
            TenureRelationship.objects.create(
                **content_types['party.tenurerelationship']
            )

    def _map_attrs_to_content_types(self, headers, row, content_types,
                                    attributes, attr_map):
        for model, selectors in attr_map.items():
            for selector, attrs in selectors.items():
                content_type = content_types.get(model, None)
                if not content_type:
                    continue
                if selector in ['DEFAULT', content_type.get('type', '')]:
                    for attr in attrs:
                        attribute = attrs[attr][0]
                        attr_label = '{0}::{1}'.format(
                            model.split('.')[1], attr)
                        if attr_label not in attributes:
                            continue
                        try:
                            val = row[headers.index(attribute.name.lower())]
                        except:
                            val = row[headers.index(attr_label)]
                        if not attribute.required and val == '':
                            continue
                        if attribute.attr_type.name == 'select_multiple':
                            val = [v.strip() for v in val.split(',')]
                        if attribute.attr_type.name in ['integer', 'decimal']:
                            val = self._cast_to_type(
                                val, attribute.attr_type.name)
                        if content_type:
                            content_type['attributes'][attribute.name] = val
        return content_types

    def _cast_to_type(self, val, type):
        if type == 'integer':
            try:
                val = int(float(val))
            except:
                val = 0
        if type == 'decimal':
            try:
                val = float(val)
            except:
                val = 0.0
        return val
