from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from party.models import TenureRelationshipType
from spatial.choices import TYPE_CHOICES
from xforms.utils import InvalidODKGeometryError, odk_geom_to_wkt


def validate_row(headers, row, config):
    party_name, party_type, geometry, tenure_type, location_type = (
        None, None, None, None, None)

    (party_name_field, party_type_field, location_type_field, type,
        geometry_field, tenure_type_field) = get_fields_from_config(config)

    if len(headers) != len(row):
        raise ValidationError(
            _("Number of headers and columns do not match.")
        )
    if party_name_field and party_type_field:
        try:
            party_name = row[headers.index(party_name_field)]
        except ValueError:
            raise ValidationError(
                _("No 'party_name' column found.")
            )
        try:
            party_type = row[headers.index(party_type_field)]
        except ValueError:
            raise ValidationError(
                _("No 'party_type' column found.")
            )
    if geometry_field:
        try:
            coords = row[headers.index(geometry_field)]
        except ValueError:
            raise ValidationError(
                _("No 'geometry_field' column found.")
            )
        try:
            geometry = GEOSGeometry(coords)
        except:
            pass  # try ODK geom parser
        if not geometry:
            try:
                geometry = odk_geom_to_wkt(coords)
            except InvalidODKGeometryError:
                raise ValidationError(_("Invalid geometry."))
    if location_type_field:
        try:
            location_type = row[headers.index(location_type_field)]
            type_choices = [choice[0] for choice in TYPE_CHOICES]
            if location_type and location_type not in type_choices:
                raise ValidationError(
                    _("Invalid location_type: '%s'.") % location_type
                )
        except ValueError:
            raise ValidationError(
                _("No 'location_type' column found.")
            )
    if party_name_field and geometry_field:
        try:
            tenure_type = row[
                headers.index(tenure_type_field)]
            if tenure_type and not TenureRelationshipType.objects.filter(
                    id=tenure_type).exists():
                raise ValidationError(
                    _("Invalid tenure_type: '%s'.") % tenure_type
                )
        except ValueError:
            raise ValidationError(
                _("No 'tenure_type' column found.")
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
