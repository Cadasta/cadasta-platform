"""Custom managers for project relationships."""

from django.db import models

from . import exceptions


class PartyManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).defer('attributes')


class BaseRelationshipManager(models.Manager):
    """
    Manager to provide project relationship checks.

    Checks that all entities belong to the same project.
    """

    def check_project_constraints(self, project=None, left=None, right=None):
        """Related entities must be in the same project."""
        if (project.id != left.project.id or
                project.id != right.project.id or
                left.project.id != right.project.id):
            raise exceptions.ProjectRelationshipError(
                'Related entities are not in the same project.')


class PartyRelationshipManager(BaseRelationshipManager):
    """Manages PartyRelationships."""

    def create(self, *args, **kwargs):
        """Check that related entities are in the same project."""
        project = kwargs['project']
        party1 = kwargs['party1']
        party2 = kwargs['party2']
        self.check_project_constraints(
            project=project, left=party1, right=party2)
        return super().create(**kwargs)


class TenureRelationshipManager(BaseRelationshipManager):
    """Manages TenureRelationships."""

    use_for_related_fields = True

    def create(self, *args, **kwargs):
        """Check that related entities are in the same project."""
        project = kwargs['project']
        party = kwargs['party']
        spatial_unit = kwargs['spatial_unit']
        assert project is not None, 'Project must be set.'
        self.check_project_constraints(
            project=project, left=party, right=spatial_unit)
        return super().create(**kwargs)

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).defer(
            'attributes').select_related('tenure_type')
