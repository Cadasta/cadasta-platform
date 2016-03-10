from django.test import TestCase

from .factories import OrganizationFactory, ProjectFactory


class OrganizationTest(TestCase):
    def test_str(self):
        org = OrganizationFactory.create(**{'name': 'Org'})
        assert str(org) == '<Organization: Org>'

    def test_has_random_id(self):
        org = OrganizationFactory.create()
        assert type(org.id) is not int


class ProjectTest(TestCase):
    def test_str(self):
        project = ProjectFactory.create(**{'name': 'Project'})
        assert str(project) == '<Project: Project>'

    def test_has_random_id(self):
        project = ProjectFactory.create()
        assert type(project.id) is not int
