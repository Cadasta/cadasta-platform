from functools import partial

from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from party.models import TenureRelationshipType
from spatial.choices import TYPE_CHOICES
from xforms.utils import InvalidODKGeometryError, odk_geom_to_wkt


def get_field_value(headers, row, header, field_name):
    try:
        return row[headers.index(header)]
    except ValueError:
        raise ValidationError(
            _("No '{}' column found.".format(field_name))
        )


def validate_row(headers, row, config):
    party_name, party_type, geometry, tenure_type, location_type = (
        None, None, None, None, None)

    (party_name_field, party_type_field, location_type_field, type,
        geometry_field, tenure_type_field) = get_fields_from_config(config)

    if len(headers) != len(row):
        raise ValidationError(
            _("Number of headers and columns do not match.")
        )

    _get_field_value = partial(get_field_value, headers, row)

    if party_name_field and party_type_field:
        party_name = _get_field_value(party_name_field, "party_name")
        party_type = _get_field_value(party_type_field, "party_type")

    if geometry_field:
        coords = _get_field_value(geometry_field, "geometry_field")
        if coords == '':
            geometry = None
        else:
            try:
                geometry = GEOSGeometry(coords)
            except:
                try:
                    geometry = GEOSGeometry(odk_geom_to_wkt(coords))
                except InvalidODKGeometryError:
                    raise ValidationError(_("Invalid geometry."))

    if location_type_field:
        location_type = _get_field_value(location_type_field, "location_type")
        type_choices = [choice[0] for choice in TYPE_CHOICES]
        if location_type and location_type not in type_choices:
            raise ValidationError(
                _("Invalid location_type: '%s'.") % location_type
            )

    if party_name_field and geometry_field:
        tenure_type = _get_field_value(tenure_type_field, 'tenure_type')
        if tenure_type and not TenureRelationshipType.objects.filter(
                id=tenure_type).exists():
            raise ValidationError(
                _("Invalid tenure_type: '%s'.") % tenure_type
            )

    return (party_name, party_type, geometry, location_type, tenure_type)


def get_fields_from_config(config):
    party_name_field = config.get('party_name_field', None)
    party_type_field = config.get('party_type_field', None)
    location_type_field = config.get('location_type_field', None)
    type = config.get('type', None)
    geometry_field = config.get('geometry_field', None)
    tenure_type_field = 'tenure_type'
    if type == 'xls':
        party_name_field = (
            'party::' + party_name_field if party_name_field else None)
        party_type_field = ('party::%s' %
                            party_type_field if party_type_field else None)
        location_type_field = (
            'spatialunit::%s' % location_type_field
            if location_type_field else None
        )
        geometry_field = (
            'spatialunit::%s' % geometry_field if geometry_field else None
        )
        tenure_type_field = (
            'tenurerelationship::%s' % tenure_type_field
            if tenure_type_field else None)
    return (
        party_name_field, party_type_field, location_type_field, type,
        geometry_field, tenure_type_field
    )
