import io
import itertools

import pandas as pd
from django.utils.translation import ugettext as _

from . import base, exceptions


class XLSImporter(base.Importer):

    EXCLUDE_IDS = [
        'id', 'party_id', 'spatial_unit_id', 'tenure_type.id',
        'tenure_type.label'
    ]

    def __init__(self, project=None, path=None):
        super(XLSImporter, self).__init__(project=project)
        self.path = path

    def get_header_map(self):
        headers = {}
        EXCLUDE_HEADERS = base.EXCLUDE_HEADERS.copy()
        EXCLUDE_HEADERS.extend(self.EXCLUDE_IDS)
        workbook = pd.read_excel(self.path, sheetname=None)
        for sheet in workbook.keys():
            worksheet = workbook[sheet]
            heads = []
            headers[sheet] = heads
            for col in worksheet.columns.tolist():
                if not (col.startswith(
                        ('_', 'meta/')) or col in EXCLUDE_HEADERS):
                    heads.append(col.lower())
        return headers

    def get_headers(self):
        return itertools.chain.from_iterable(self.get_header_map().values())

    def import_data(self, config, **kwargs):
        entity_types = config['entity_types']
        df = pd.read_excel(self.path, sheetname=None)
        data = get_csv_from_dataframe(df, entity_types)
        with io.StringIO(data) as csvfile:
            self._import(config, csvfile)


def get_csv_from_dataframe(df, entity_types):
    locations, parties, relationships = None, None, None
    try:
        if 'SU' in entity_types and 'PT' in entity_types:
            locations = df['locations']
            parties = df['parties']
            relationships = df['relationships']
            if not (locations.empty or
                    relationships.empty or parties.empty):
                locations.rename(
                    columns=lambda x: 'spatialunit::' + x.lower(),
                    inplace=True
                )
                relationships.rename(
                    columns={'tenure_type.id': 'tenure_type'},
                    inplace=True
                )
                relationships.rename(
                    columns=lambda x: 'tenurerelationship::' + x.lower(),
                    inplace=True)
                parties.rename(
                    columns=lambda x: 'party::' + x.lower(), inplace=True
                )
                # join locations and relationships on spatial_id's
                joined = pd.merge(
                    locations, relationships, left_on='spatialunit::id',
                    right_on='tenurerelationship::spatial_unit_id',
                    how='outer'
                )
                # then join to parties on party_id
                merged = pd.merge(
                    joined, parties, left_on='tenurerelationship::party_id',
                    right_on='party::id', how='outer'
                )
                # drop unused columns
                drop_cols = [
                    'spatialunit::id', 'party::id',
                    'tenurerelationship::tenure_type.label'
                ]
                merged.drop(drop_cols, inplace=True, axis=1)

                return merged.to_csv(index=False, index_label=False)
            else:
                raise exceptions.DataImportError(
                    _('Empty worksheet.'))
        elif 'SU' in entity_types and 'PT' not in entity_types:
            locations = df['locations']
            # rename location type
            locations.rename(
                columns=lambda x: 'spatialunit::' + x.lower(), inplace=True
            )
            drop_cols = ['spatialunit::id']
            locations.drop(drop_cols, inplace=True, axis=1)
            return locations.to_csv(index=False, index_label=False)
        elif 'SU' not in entity_types and 'PT' in entity_types:
            parties = df['parties']
            parties.rename(
                columns=lambda x: 'party::' + x.lower(), inplace=True
            )
            drop_cols = ['party::id']
            parties.drop(drop_cols, inplace=True, axis=1)
            return parties.to_csv(index=False, index_label=False)
        else:
            raise exceptions.DataImportError(
                _('Unsupported import format.'))
    except KeyError as e:
        raise exceptions.DataImportError(
            _("Missing '%s' worksheet.") % e.args[0])
