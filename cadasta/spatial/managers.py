from django.db import models

from . import models as spatial_models
from .exceptions import SpatialRelationshipError
from party.managers import BaseRelationshipManager


class SpatialUnitManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).defer('attributes')


class SpatialRelationshipManager(BaseRelationshipManager):
    """Check conditions based on spatial unit type before creating
    object. If conditions aren't met, exceptions are raised."""

    def create(self, *args, **kwargs):
        su1 = kwargs['su1']
        su2 = kwargs['su2']
        project = kwargs['project']
        if (su1.geometry is not None and
                su2.geometry is not None):

            if (kwargs['type'] == 'C' and
                    su1.geometry.geom_type == 'Polygon'):
                result = spatial_models.SpatialUnit.objects.filter(
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
