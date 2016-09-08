"""Party models."""

from core.models import RandomIDModel
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext as _

from jsonattrs.decorators import fix_model_for_attributes
from jsonattrs.fields import JSONAttributeField
from organization.models import Project
from organization.validators import validate_contact
from simple_history.models import HistoricalRecords

from resources.mixins import ResourceModelMixin
from spatial.models import SpatialUnit
from tutelary.decorators import permissioned_model

from . import managers, messages

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


@fix_model_for_attributes
@permissioned_model
class Party(ResourceModelMixin, RandomIDModel):
    """
    Party model.

    A single party: has a name, a type, a type-dependent set of
    attributes and relationships with other parties and spatial units
    (i.e. tenure relationships).

    """

    # Possible party types: TYPE_CHOICES is the well-known name used
    # by the JSONAttributesField field type to manage the range of
    # allowed attribute fields.
    INDIVIDUAL = 'IN'
    CORPORATION = 'CO'
    GROUP = 'GR'
    TYPE_CHOICES = ((INDIVIDUAL, _('Individual')),
                    (CORPORATION, _('Corporation')),
                    (GROUP, _('Group')))

    # All parties are associated with a single project.
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='parties')

    # All parties have a name: for individuals, this is the full name,
    # while for groups and corporate entities, it's whatever name is
    # conventionally used to identify the organisation.
    name = models.CharField(max_length=200)

    # Party type: used to manage range of allowed attributes.
    type = models.CharField(
        max_length=2, choices=TYPE_CHOICES, default=INDIVIDUAL)

    contacts = JSONField(validators=[validate_contact], default={})

    # JSON attributes field with management of allowed members.
    attributes = JSONAttributeField(default={})

    # Party-party relationships: includes things like family
    # relationships and group memberships.
    relationships = models.ManyToManyField(
        'self',
        through='PartyRelationship',
        through_fields=('party1', 'party2'),
        symmetrical=False,
        related_name='relationships_set'
    )

    # Tenure relationships.
    tenure_relationships = models.ManyToManyField(
        SpatialUnit,
        through='TenureRelationship',
        related_name='tenure_relationships'
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'party'
        path_fields = ('project', 'id')
        actions = (
            ('party.list',
             {'description': _("List existing parties of a project"),
              'error_message': messages.PARTY_LIST,
              'permissions_object': 'project'}),
            ('party.create',
             {'description': _("Add a party to a project"),
              'error_message': messages.PARTY_CREATE,
              'permissions_object': 'project'}),
            ('party.view',
             {'description': _("View an existing party"),
              'error_message': messages.PARTY_VIEW}),
            ('party.update',
             {'description': _("Update an existing party"),
              'error_message': messages.PARTY_UPDATE}),
            ('party.delete',
             {'description': _("Delete an existing party"),
              'error_message': messages.PARTY_DELETE}),
            ('party.resources.add',
             {'description': _("Add resources to the party"),
              'error_message': messages.PARTY_RESOURCES_ADD})
        )

    def __str__(self):
        return "<Party: {}>".format(self.name)

    def __repr__(self):
        return str(self)

    @property
    def ui_class_name(self):
        return _("Party")

    @property
    def ui_detail_url(self):
        return reverse(
            'parties:detail',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'party': self.id,
            },
        )


@fix_model_for_attributes
@permissioned_model
class PartyRelationship(RandomIDModel):
    """
    PartyRelationship model.

    A relationship between parties: encodes simple logical terms like
    ``party1 is-spouse-of party2`` or ``party1 is-member-of party2``.
    May have additional type-dependent attributes.

    """

    # Possible party relationship types: TYPE_CHOICES is the
    # well-known name used by the JSONAttributesField field type to
    # manage the range of allowed attribute fields.
    TYPE_CHOICES = (('S', 'is-spouse-of'),
                    ('C', 'is-child-of'),
                    ('M', 'is-member-of'))

    # All party relationships are associated with a single project
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='party_relationships')

    # Parties to the relationship.
    party1 = models.ForeignKey(Party, on_delete=models.CASCADE,
                               related_name='party1')
    party2 = models.ForeignKey(Party, on_delete=models.CASCADE,
                               related_name='party2')

    # Party relationship type: used to manage range of allowed attributes.
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    # JSON attributes field with management of allowed members.
    attributes = JSONAttributeField(default={})

    objects = managers.PartyRelationshipManager()

    history = HistoricalRecords()

    class TutelaryMeta:
        perm_type = 'party_rel'
        path_fields = ('project', 'id')
        actions = (
            ('party_rel.list',
             {'description': _("List existing party relationships"
                               " of a project"),
              'error_message': messages.PARTY_REL_LIST,
              'permissions_object': 'project'}),
            ('party_rel.create',
             {'description': _("Add a party relationship to a project"),
              'error_message': messages.PARTY_REL_CREATE,
              'permissions_object': 'project'}),
            ('party_rel.view',
             {'description': _("View an existing party relationship"),
              'error_message': messages.PARTY_REL_VIEW}),
            ('party_rel.update',
             {'description': _("Update an existing party relationship"),
              'error_message': messages.PARTY_REL_UPDATE}),
            ('party_rel.delete',
             {'description': _("Delete an existing party relationship"),
              'error_message': messages.PARTY_REL_DELETE}),
        )

    def __str__(self):
        return "<PartyRelationship: <{party1}> {type} <{party2}>>".format(
            party1=self.party1.name, party2=self.party2.name,
            type=dict(self.TYPE_CHOICES).get(self.type))

    def __repr__(self):
        return str(self)


@fix_model_for_attributes
@permissioned_model
class TenureRelationship(ResourceModelMixin, RandomIDModel):
    """TenureRelationship model.

    Governs relationships between Party and SpatialUnit.
    """

    CONTRACTUAL_SHARE_CROP = 'CS'
    CUSTOMARY_ARRANGEMENT = 'CA'
    GIFT = 'GF'
    HOMESTEAD = 'HS'
    INFORMAL_OCCUPANT = 'IO'
    INHERITANCE = 'IN'
    LEASEHOLD = 'LH'
    PURCHASED_FREEHOLD = 'PF'
    RENTAL = 'RN'
    OTHER = 'OT'

    ACQUIRED_CHOICES = ((CONTRACTUAL_SHARE_CROP, _('Contractual/Share Crop')),
                        (CUSTOMARY_ARRANGEMENT, _('Customary Arrangement')),
                        (GIFT, _('Gift')),
                        (HOMESTEAD, _('Homestead')),
                        (INFORMAL_OCCUPANT, _('Informal Occupant')),
                        (INHERITANCE, _('Inheritance')),
                        (LEASEHOLD, _('Leasehold')),
                        (PURCHASED_FREEHOLD, _('Purchased Freehold')),
                        (RENTAL, _('Rental')),
                        (OTHER, _('Other')))

    # All tenure relationships are associated with a single project
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='tenure_relationships')

    # Party to the relationship
    party = models.ForeignKey(Party, on_delete=models.CASCADE)

    # Spatial unit in the relationship
    spatial_unit = models.ForeignKey(SpatialUnit, on_delete=models.CASCADE)

    # Tenure relationships type: used to manage range of allowed attributes
    tenure_type = models.ForeignKey(
        'TenureRelationshipType',
        related_name='tenure_type', null=False, blank=False
    )

    # JSON attributes field with management of allowed members.
    attributes = JSONAttributeField(default={})
    objects = managers.TenureRelationshipManager()

    history = HistoricalRecords()

    class TutelaryMeta:
        perm_type = 'tenure_rel'
        path_fields = ('project', 'id')
        actions = (
            ('tenure_rel.list',
             {'description': _("List existing tenure relationships"
                               " of a project"),
              'error_message': messages.TENURE_REL_LIST,
              'permissions_object': 'project'}),
            ('tenure_rel.create',
             {'description': _("Add a tenure relationship to a project"),
              'error_message': messages.TENURE_REL_CREATE,
              'permissions_object': 'project'}),
            ('tenure_rel.view',
             {'description': _("View an existing tenure relationship"),
              'error_message': messages.TENURE_REL_VIEW}),
            ('tenure_rel.update',
             {'description': _("Update an existing tenure relationship"),
              'error_message': messages.TENURE_REL_UPDATE}),
            ('tenure_rel.delete',
             {'description': _("Delete an existing tenure relationship"),
              'error_message': messages.TENURE_REL_DELETE}),
            ('tenure_rel.resources.add',
             {'description': _("Add a resource to a tenure relationship"),
              'error_message': messages.TENURE_REL_RESOURCES_ADD}),
        )

    def __str__(self):
        return "<TenureRelationship: {}>".format(self.name)

    def __repr__(self):
        return str(self)

    @property
    def name(self):
        return "<{party}> {type} <{su}>".format(
            party=self.party.name,
            su=self.spatial_unit.name,
            type=self.tenure_type.label,
        )

    @property
    def ui_class_name(self):
        return _("Relationship")

    @property
    def ui_detail_url(self):
        return reverse(
            'parties:relationship_detail',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'relationship': self.id,
            },
        )


class TenureRelationshipType(models.Model):
    """Defines allowable tenure types."""

    id = models.CharField(max_length=2, primary_key=True)
    label = models.CharField(max_length=200)

    history = HistoricalRecords()


TENURE_RELATIONSHIP_TYPES = (
    ('CR', 'Carbon Rights'),
    ('CO', 'Concessionary Rights'),
    ('CU', 'Customary Rights'),
    ('EA', 'Easement'),
    ('ES', 'Equitable Servitude'),
    ('FH', 'Freehold'),
    ('GR', 'Grazing Rights'),
    ('HR', 'Hunting/Fishing/Harvest Rights'),
    ('IN', 'Indigenous Land Rights'),
    ('JT', 'Joint Tenancy'),
    ('LH', 'Leasehold'),
    ('LL', 'Longterm Leasehold'),
    ('MR', 'Mineral Rights'),
    ('OC', 'Occupancy (No Documented Rights)'),
    ('TN', 'Tenancy (Documented Sub-lease)'),
    ('TC', 'Tenancy In Common'),
    ('UC', 'Undivided Co-ownership'),
    ('WR', 'Water Rights')
)


def load_tenure_relationship_types(force=False):
    if force:
        TenureRelationshipType.objects.all().delete()
    for tr_type in TENURE_RELATIONSHIP_TYPES:
        if not TenureRelationshipType.objects.filter(
                id=tr_type[0], label=tr_type[1]
        ).exists():
            TenureRelationshipType.objects.create(
                id=tr_type[0], label=tr_type[1]
            )
