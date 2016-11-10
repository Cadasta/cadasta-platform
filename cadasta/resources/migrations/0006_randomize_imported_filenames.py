from __future__ import unicode_literals

import os

from core.util import random_id
from django.db import migrations


def fix_original_file_field(apps, schema_editor):
    Resource = apps.get_model("resources", "Resource")
    resources = Resource.objects.filter(mime_type='text/csv')
    for resource in resources:
        url = resource.file.url
        if url.endswith('.csv'):
            parts = list(os.path.split(url))
            if not resource.original_file:
                resource.original_file = parts[-1]
                resource.save()


def randomize_imported_resource_filenames(apps, schema_editor):
    Resource = apps.get_model("resources", "Resource")
    resources = Resource.objects.filter(mime_type='text/csv')
    for resource in resources:
        url = resource.file.url
        if url.endswith('.csv'):
            random_filename = '/' + random_id() + '.csv'
            parts = list(os.path.split(url))
            base_url = parts[:-1]
            url = '/'.join(base_url) + random_filename
            resource.file.url = url
            resource.save()


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_fix_import_resource_urls'),
    ]

    operations = [
        migrations.RunPython(
            fix_original_file_field, migrations.RunPython.noop),
        migrations.RunPython(
            randomize_imported_resource_filenames, migrations.RunPython.noop),
    ]
