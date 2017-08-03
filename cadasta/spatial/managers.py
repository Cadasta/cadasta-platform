from .exceptions import SpatialRelationshipError
from party.managers import BaseRelationshipManager


class SpatialRelationshipManager(BaseRelationshipManager):
    """Check conditions based on spatial unit type before creating
    object. If conditions aren't met, exceptions are raised."""

    def create(self, *args, **kwargs):
        su1 = kwargs['su1']
        su2 = kwargs['su2']
        project = kwargs['project']
        rel_error = (
            kwargs['type'] == 'C' and
            su1.geometry is not None and
            su2.geometry is not None and
            su1.geometry.geom_type == 'Polygon' and
            not su1.geometry.contains(su2.geometry)
        )
        if rel_error:
            raise SpatialRelationshipError(
                "That selected location is not geographically "
                "contained within the parent location")
        self.check_project_constraints(
            project=project, left=su1, right=su2)
        return super().create(**kwargs)
