import factory

from core.tests.factories import ExtendedFactory
from spatial.models import SpatialUnit, SpatialUnitRelationship
from organization.tests.factories import ProjectFactory


class SpatialUnitFactory(ExtendedFactory):
    class Meta:
        model = SpatialUnit

    name = factory.Sequence(lambda n: "Location #{}".format(n))
    project = factory.SubFactory(ProjectFactory)


class SpatialUnitRelationshipFactory(ExtendedFactory):
    class Meta:
        model = SpatialUnitRelationship

    project = factory.SubFactory(ProjectFactory)
    su1 = factory.SubFactory(SpatialUnitFactory, project=project)
    su2 = factory.SubFactory(SpatialUnitFactory, project=project)
    type = 'C'
