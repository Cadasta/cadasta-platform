from django.test import TestCase
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader


class MigrationTestCase(TestCase):
    migrate_from = '0005_add_area_to_project'
    migrate_to = '0006_add_project_area_trigger'

    def _get_apps_for_migration(self, migration_states):
        loader = MigrationLoader(connection)
        full_names = []
        for app_name, migration_name in migration_states:
            if migration_name != 'zero':
                migration_name = loader.get_migration_by_prefix(
                    app_name, migration_name).name
                full_names.append((app_name, migration_name))
        state = loader.project_state(full_names)
        return state.apps

    def test_migration(self):
        apps_before = self._get_apps_for_migration([
            ('organization', self.migrate_from),
            ('spatial', '0005_recalculate_area')])
        Organization = apps_before.get_model('organization', 'Organization')
        Project = apps_before.get_model('organization', 'Project')
        SpatialUnit = apps_before.get_model('spatial', 'SpatialUnit')

        call_command('migrate', 'organization', self.migrate_from)

        org = Organization.objects.create(name='Test Org')
        project = Project.objects.create(name='Test Proj', organization=org)

        su1 = SpatialUnit.objects.create(
            id='abc',
            project=project,
            type='PA',
            geometry='POLYGON((12.323006 51.327645,12.322913 '
                     '51.327355,12.323114 51.327330,12.323189 '
                     '51.327624,12.323006 51.327645))')
        su1.refresh_from_db()
        su2 = SpatialUnit.objects.create(
            id='def',
            project=project,
            type='PA',
            geometry='POLYGON((12.323041 51.32775,12.323012 '
                     '51.327661,12.323197 51.327638,12.323224 '
                     '51.327727,12.323041 51.32775))')
        su2.refresh_from_db()

        call_command('migrate', 'organization', self.migrate_to)

        project.refresh_from_db()
        assert project.area == sum((su1.area, su2.area))
