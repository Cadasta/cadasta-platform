import factory
from core.tests.factories import ExtendedFactory
from organization.tests.factories import ProjectFactory
from spatial.models import SpatialUnit, SpatialRelationship


class SpatialUnitFactory(ExtendedFactory):

    class Meta:
        model = SpatialUnit

    project = factory.SubFactory(ProjectFactory)
    type = 'PA'


class SpatialRelationshipFactory(ExtendedFactory):

    class Meta:
        model = SpatialRelationship

    project = factory.SubFactory(ProjectFactory)
    su1 = factory.SubFactory(
        SpatialUnitFactory, project=factory.SelfAttribute('..project'))
    su2 = factory.SubFactory(
        SpatialUnitFactory, project=factory.SelfAttribute('..project'))
    type = 'C'
