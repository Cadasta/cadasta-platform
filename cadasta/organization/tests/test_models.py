from django.test import TestCase

from .factories import OrganizationFactory


class OrganizationTest(TestCase):
    def test_str(self):
        org = OrganizationFactory.create(**{'name': 'Org'})
        assert str(org) == '<Organization: Org>'

    def test_has_random_id(self):
        org = OrganizationFactory.create()
        assert type(org.id) is not int
