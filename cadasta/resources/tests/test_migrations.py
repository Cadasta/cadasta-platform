from core.tests.utils.cases import UserTestCase
from core.util import random_id
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase


class MigrationTestCase(UserTestCase, TestCase):

    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    migrate_from = None
    migrate_to = None

    def setUp(self):
        super(UserTestCase, self).setUp()

        assert self.migrate_from and self.migrate_to
        "TestCase '{}' must define migrate_from and migrate_to "
        "properties".format(type(self).__name__)

        # get the application state pre-migration
        apps_before = self._get_apps_for_migration(
            [(self.app, self.migrate_from)])

        # Reverse to migrate_from
        call_command('migrate', 'accounts',
                     '0002_activate_users_20161014_0846')
        call_command('migrate', 'organization',
                     '0004_remove_Pb_project_roles')
        call_command('migrate', self.app, self.migrate_from)

        # setup pre-migration test data
        self.setUpBeforeMigration(apps_before)

        # Run the migration to test
        call_command('migrate', self.app, self.migrate_to)

        # get application state post-migration
        self.apps_after = self._get_apps_for_migration(
            [(self.app, self.migrate_to)])

    def setUpBeforeMigration(self, apps):
        pass

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


class TestFixImportedResourceUrls(MigrationTestCase):

    migrate_from = '0004_add_ordering_for_resources'
    migrate_to = '0005_fix_import_resource_urls'

    def setUpBeforeMigration(self, apps_before):
        Resource = apps_before.get_model('resources', 'Resource')
        User = apps_before.get_model('accounts', 'User')
        Organization = apps_before.get_model('organization', 'Organization')
        Project = apps_before.get_model('organization', 'Project')

        user = User.objects.create(username='testuser')
        org = Organization.objects.create(name='Test Org')
        project = Project.objects.create(name='Test Proj', organization=org)

        base_path = (
            'https://s3-us-west-2.amazonaws.com/cadasta-resources/'
        )

        # cannot call custom save methods on models in migrations
        # as models are serialized from migration scripts
        # so custom methods are not available
        # docs.djangoproject.com/en/1.9/topics/migrations/#historical-models
        for f in range(10):
            file_name = base_path + 'test_' + str(f) + '.csv'
            resource_name = 'test-resource-' + str(f)
            Resource.objects.create(
                id=random_id(), name=resource_name, file=file_name,
                mime_type='text/csv', contributor=user, project=project
            )
        Resource.objects.create(
            id=random_id(), file=base_path + 'test.jpg', mime_type='image/jpg',
            contributor=user, project=project
        )

    def test_migration(self):
        Resource = self.apps_after.get_model('resources', 'Resource')
        resources = Resource.objects.filter(mime_type='text/csv')
        assert len(resources) == 10
        base_path = (
            'https://s3-us-west-2.amazonaws.com/cadasta-resources/'
        )
        resource = Resource.objects.get(name='test-resource-0')
        assert resource.file.url == base_path + 'resources/test_0.csv'


class TestRandomizeImportedFilenames(MigrationTestCase):
    migrate_from = '0005_fix_import_resource_urls'
    migrate_to = '0006_randomize_imported_filenames'

    def setUpBeforeMigration(self, apps_before):
        Resource = apps_before.get_model('resources', 'Resource')
        User = apps_before.get_model('accounts', 'User')
        Organization = apps_before.get_model('organization', 'Organization')
        Project = apps_before.get_model('organization', 'Project')

        user = User.objects.create(username='testuser')
        org = Organization.objects.create(name='Test Org')
        project = Project.objects.create(name='Test Proj', organization=org)

        base_path = (
            'https://s3-us-west-2.amazonaws.com/cadasta-resources/'
            'resources/'
        )

        for f in range(10):
            file_name = base_path + 'test_' + str(f) + '.csv'
            resource_name = 'test-resource-' + str(f)
            Resource.objects.create(
                id=random_id(), name=resource_name, file=file_name,
                mime_type='text/csv', contributor=user, project=project
            )
        Resource.objects.create(
            id=random_id(), file=base_path + 'test.jpg', mime_type='image/jpg',
            contributor=user, project=project
        )

    def test_migration(self):
        Resource = self.apps_after.get_model('resources', 'Resource')
        resources = Resource.objects.filter(mime_type='text/csv')
        assert len(resources) == 10
        resource = Resource.objects.get(name='test-resource-0')
        assert resource.original_file == 'test_0.csv'
        random_filename = resource.file.url[resource.file.url.rfind('/'):]
        assert random_filename.endswith('.csv')
        assert len(random_filename.split('.')[0].strip('/')) == 24
