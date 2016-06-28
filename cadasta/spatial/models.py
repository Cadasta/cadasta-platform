from core.models import RandomIDModel
from django.contrib.gis.db.models import GeometryField
from django.db import models
from django.utils.translation import ugettext as _
from organization.models import Project
from party import managers
from tutelary.decorators import permissioned_model
from simple_history.models import HistoricalRecords

from . import messages
from .choices import TYPE_CHOICES
from .exceptions import SpatialUnitRelationshipError
from jsonattrs.fields import JSONAttributeField
from jsonattrs.decorators import fix_model_for_attributes


@fix_model_for_attributes
@permissioned_model
class SpatialUnit(RandomIDModel):
    """A single spatial unit: has a type, an optional geometry, a
    type-dependent set of attributes, and a set of relationships to
    other spatial units.

    """

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'spatial'
        path_fields = ('project', 'id')
        actions = (
            ('spatial.list',
             {'description': _("List existing spatial units in a project"),
              'error_message': messages.SPATIAL_LIST,
              'permissions_object': 'project'}),
            ('spatial.add',
             {'description': _("Add a spatial units in a project"),
              'error_message': messages.SPATIAL_ADD,
              'permissions_object': 'project'}),
            ('spatial.view',
             {'description': _("View existing spatial unit in project"),
              'error_message': messages.SPATIAL_VIEW,
              'permissions_object': 'project'}),
            ('spatial.update',
             {'description': _("Updated an existing spatial unit in project"),
              'error_message': messages.SPATIAL_EDIT,
              'permissions_object': 'project'}),
            ('spatial.delete',
             {'description': _("Delete spatial unit from a project"),
              'error_message': messages.SPATIAL_REMOVE,
              'permissions_object': 'project'}),
        )

    # All spatial units are associated with a single project.
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='spatial_units')

    name = models.CharField(max_length=200)

    # Spatial unit geometry is optional: some spatial units may only
    # have a textual description of their location.
    geometry = GeometryField(null=True)

    # Spatial unit type: used to manage range of allowed attributes.
    type = models.CharField(max_length=2,
                            choices=TYPE_CHOICES, default='PA')

    # JSON attributes field with management of allowed members.
    attributes = JSONAttributeField(default={})

    # Spatial unit-spatial unit relationships: includes spatial
    # containment and split/merge relationships.
    relationships = models.ManyToManyField(
        'self',
        through='SpatialUnitRelationship',
        through_fields=('su1', 'su2'),
        symmetrical=False,
        related_name='relationships_set',
    )

    history = HistoricalRecords()

    def __str__(self):
        return "<SpatialUnit: {name}>".format(name=self.name)


class SpatialUnitRelationshipManager(managers.BaseRelationshipManager):
    """Check conditions based on spatial unit type before creating
    object. If conditions aren't met, exceptions are raised.

    """

    def create(self, *args, **kwargs):
        su1 = kwargs['su1']
        su2 = kwargs['su2']
        project = kwargs['project']
        if (su1.geometry is not None and
                su2.geometry is not None):

            if (kwargs['type'] == 'C' and
                    su1.geometry.geom_type == 'Polygon'):
                result = SpatialUnit.objects.filter(
                    id=su1.id
                ).filter(
                    geometry__contains=su2.geometry
                )

                if len(result) != 0:
                    self.check_project_constraints(
                        project=project, left=su1, right=su2)
                    return super().create(**kwargs)
                else:
                    raise SpatialUnitRelationshipError(
                        """That selected location is not geographically
                        contained within the parent location""")
        self.check_project_constraints(
            project=project, left=su1, right=su2)
        return super().create(**kwargs)


@fix_model_for_attributes
class SpatialUnitRelationship(RandomIDModel):
    """A relationship between spatial units: encodes simple logical terms
    like ``su1 is-contained-in su2`` or ``su1 is-split-of su2``.  May
    have additional requirements.

    """

    # Possible spatial unit relationships types: TYPE_CHOICES is the
    # well-known name used by the JSONAttributesField field type to
    # manage the range of allowed attribute fields.
    TYPE_CHOICES = (('C', 'is-contained-in'),
                    ('S', 'is-split-of'),
                    ('M', 'is-merge-of'))

    # All spatial unit relationships are associated with a single project.
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    # Spatial units are in the relationships.
    su1 = models.ForeignKey(SpatialUnit, on_delete=models.CASCADE,
                            related_name='spatial_unit_one')
    su2 = models.ForeignKey(SpatialUnit, on_delete=models.CASCADE,
                            related_name='spatial_unit_two')

    # Spatial unit relationship type: used to manage range of allowed
    # attributes
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    # JSON attributes field with management of allowed members.
    attributes = JSONAttributeField(default={})
    objects = SpatialUnitRelationshipManager()

    history = HistoricalRecords()
