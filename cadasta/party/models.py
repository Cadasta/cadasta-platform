"""Party models."""

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.postgres.fields import JSONField

from core.models import RandomIDModel

from tutelary.decorators import permissioned_model
from organization.models import Project
from organization.validators import validate_contact

from . import messages

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


@permissioned_model
class Party(RandomIDModel):
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
    TYPE_CHOICES = ((INDIVIDUAL, 'Individual'),
                    (CORPORATION, 'Corporation'),
                    (GROUP, 'Group'))

    # All parties are associated with a single project.
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='parties')

    # All parties have a name: for individuals, this is the full name,
    # while for groups and corporate entities, it's whatever name is
    # conventionally used to identify the organisation.
    name = models.CharField(max_length=200)

    # Party type: used to manage range of allowed attributes.
    type = models.CharField(max_length=2,
                            choices=TYPE_CHOICES, default=INDIVIDUAL)

    contacts = JSONField(validators=[validate_contact], default={})

    # JSON attributes field with management of allowed members.
    attributes = JSONField(default={})

    # Party-party relationships: includes things like family
    # relationships and group memberships.
    relationships = models.ManyToManyField(
        'self', through='PartyRelationship',
        through_fields=('party1', 'party2'),
        symmetrical=False,
        related_name='relationships_set'
    )

    # Tenure relationships.
    # tenure_relationships = models.ManyToManyField(
    #     'SpatialUnit', through='TenureRelationship',
    #     related_name='tenure_relationships_set'
    # )

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('id',)
        actions = (
            ('project.party.list',
             {'description': _("List existing parties"), }),
            ('project.party.create',
             {'description': _("Create parties"), }),
            ('project.party.view',
             {'description': _("View existing parties"),
              'error_message': messages.PARTY_VIEW}),
            ('project.party.update',
             {'description': _("Update an existing party"),
              'error_message': messages.PARTY_EDIT}),
            # ('party.archive',
            #  {'description': _("Archive an existing party"),
            #   'error_message': messages.PARTY_ARCHIVE}),
            # ('party.unarchive',
            #  {'description': _("Unarchive an existing party"),
            #   'error_message': messages.PARTY_UNARCHIVE}),
        )

    def __str__(self):
        return "<Party: {name}>".format(name=self.name)

    def __repr__(self):
        return str(self)


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

    # All party relationships are associated with a single project.
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # Parties to the relationship.
    party1 = models.ForeignKey(Party,
                               on_delete=models.CASCADE,
                               related_name='party1'
                               )
    party2 = models.ForeignKey(Party,
                               on_delete=models.CASCADE,
                               related_name='party2')

    # Party relationship type: used to manage range of allowed attributes.
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    # JSON attributes field with management of allowed members.
    attributes = JSONField(default={})
