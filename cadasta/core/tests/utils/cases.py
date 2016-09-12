from core.tests.factories import PolicyFactory
from jsonattrs.models import create_attribute_types
from party.models import load_tenure_relationship_types


class UserTestCase:
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        create_attribute_types()
        load_tenure_relationship_types(force=True)
