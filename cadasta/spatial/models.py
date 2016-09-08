from core.models import RandomIDModel
from django.core.urlresolvers import reverse
from django.contrib.gis.db.models import GeometryField
from django.db import models
from django.utils.translation import ugettext as _
from django.dispatch import receiver
from organization.models import Project
from party import managers
from tutelary.decorators import permissioned_model
from simple_history.models import HistoricalRecords
from shapely.geometry import Point, Polygon, LineString
from shapely.wkt import dumps

from . import messages
from .choices import TYPE_CHOICES
from .exceptions import SpatialRelationshipError
from resources.mixins import ResourceModelMixin
from jsonattrs.fields import JSONAttributeField
from jsonattrs.decorators import fix_model_for_attributes


@fix_model_for_attributes
@permissioned_model
class SpatialUnit(ResourceModelMixin, RandomIDModel):
    """A single spatial unit: has a type, an optional geometry, a
    type-dependent set of attributes, and a set of relationships to
    other spatial units.

    """

    # All spatial units are associated with a single project.
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='spatial_units')

    # Spatial unit type: used to manage range of allowed attributes.
    type = models.CharField(max_length=2,
                            choices=TYPE_CHOICES, default='PA')

    # Spatial unit geometry is optional: some spatial units may only
    # have a textual description of their location.
    geometry = GeometryField(null=True)

    # JSON attributes field with management of allowed members.
    attributes = JSONAttributeField(default={})

    # Spatial unit-spatial unit relationships: includes spatial
    # containment and split/merge relationships.
    relationships = models.ManyToManyField(
        'self',
        through='SpatialRelationship',
        through_fields=('su1', 'su2'),
        symmetrical=False,
        related_name='relationships_set',
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ('type',)

    class TutelaryMeta:
        perm_type = 'spatial'
        path_fields = ('project', 'id')
        actions = (
            ('spatial.list',
             {'description': _("List existing spatial units of a project"),
              'error_message': messages.SPATIAL_LIST,
              'permissions_object': 'project'}),
            ('spatial.create',
             {'description': _("Add a spatial unit to a project"),
              'error_message': messages.SPATIAL_CREATE,
              'permissions_object': 'project'}),
            ('spatial.view',
             {'description': _("View an existing spatial unit"),
              'error_message': messages.SPATIAL_VIEW}),
            ('spatial.update',
             {'description': _("Update an existing spatial unit"),
              'error_message': messages.SPATIAL_UPDATE}),
            ('spatial.delete',
             {'description': _("Delete an existing spatial unit"),
              'error_message': messages.SPATIAL_DELETE}),
            ('spatial.resources.add',
             {'description': _("Add resources to this spatial unit"),
              'error_message': messages.SPATIAL_ADD_RESOURCE})
        )

    def __str__(self):
        return "<SpatialUnit: {}>".format(self.name)

    def __repr__(self):
        return str(self)

    @property
    def name(self):
        return self.get_type_display()

    @property
    def ui_class_name(self):
        return _("Location")

    @property
    def ui_detail_url(self):
        return reverse(
            'locations:detail',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'location': self.id,
            },
        )


def reassign_spatial_geometry(instance):
    coords = list(instance.geometry.coords)
    if type(coords[0]) == float:
        coords = [coords]
    else:
        while (type(coords[0][0]) != float):
            coords = coords[0]
        coords = [list(x) for x in coords]
    for point in coords:
        if point[0] >= -180 and point[0] <= 180:
            return
    while coords[0][0] < -180:
        for point in coords:
            point[0] += 360
    while coords[0][0] > 180:
        for point in coords:
            point[0] -= 360
    geometry = []
    for point in coords:
        latlng = [point[0], point[1]]
        geometry.append(tuple(latlng))
    if len(geometry) > 1:
        if geometry[0] == geometry[-1]:
            instance.geometry = dumps(Polygon(geometry))
        else:
            instance.geometry = dumps(LineString(geometry))
    else:
        instance.geometry = dumps(Point(geometry))


@receiver(models.signals.pre_save, sender=SpatialUnit)
def check_extent(sender, instance, **kwargs):
    if instance.geometry:
        reassign_spatial_geometry(instance)


class SpatialRelationshipManager(managers.BaseRelationshipManager):
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
                    raise SpatialRelationshipError(
                        """That selected location is not geographically
                        contained within the parent location""")
        self.check_project_constraints(
            project=project, left=su1, right=su2)
        return super().create(**kwargs)


@fix_model_for_attributes
@permissioned_model
class SpatialRelationship(RandomIDModel):
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
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='spatial_relationships')

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
    objects = SpatialRelationshipManager()

    history = HistoricalRecords()

    class TutelaryMeta:
        perm_type = 'spatial_rel'
        path_fields = ('project', 'id')
        actions = (
            ('spatial_rel.list',
             {'description': _("List existing spatial relationships"
                               " of a project"),
              'error_message': messages.SPATIAL_REL_LIST,
              'permissions_object': 'project'}),
            ('spatial_rel.create',
             {'description': _("Add a spatial relationship to a project"),
              'error_message': messages.SPATIAL_REL_CREATE,
              'permissions_object': 'project'}),
            ('spatial_rel.view',
             {'description': _("View an existing spatial relationship"),
              'error_message': messages.SPATIAL_REL_VIEW}),
            ('spatial_rel.update',
             {'description': _("Update an existing spatial relationship"),
              'error_message': messages.SPATIAL_REL_UPDATE}),
            ('spatial_rel.delete',
             {'description': _("Delete an existing spatial relationship"),
              'error_message': messages.SPATIAL_REL_DELETE}),
        )

    def __str__(self):
        return "<SpatialRelationship: <{su1}> {type} <{su2}>>".format(
            su1=self.su1.get_type_display(), su2=self.su2.get_type_display(),
            type=dict(self.TYPE_CHOICES).get(self.type))

    def __repr__(self):
        return str(self)
