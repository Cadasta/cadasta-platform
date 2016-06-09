import factory
from core.tests.factories import ExtendedFactory
from organization.tests.factories import ProjectFactory
from spatial.models import SpatialUnit, SpatialUnitRelationship


class SpatialUnitFactory(ExtendedFactory):

    class Meta:
        model = SpatialUnit

    name = factory.Sequence(lambda n: "Location #{}".format(n))
    project = factory.SubFactory(ProjectFactory)


class SpatialUnitRelationshipFactory(ExtendedFactory):

    class Meta:
        model = SpatialUnitRelationship

    project = factory.SubFactory(ProjectFactory)
    su1 = factory.SubFactory(
        SpatialUnitFactory, project=factory.SelfAttribute('..project'))
    su2 = factory.SubFactory(
        SpatialUnitFactory, project=factory.SelfAttribute('..project'))
    type = 'C'
