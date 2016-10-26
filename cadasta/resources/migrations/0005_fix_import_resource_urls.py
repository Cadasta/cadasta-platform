from __future__ import unicode_literals

import os

from django.db import migrations


def fix_imported_resource_urls(apps, schema_editor):
    Resource = apps.get_model("resources", "Resource")
    resources = Resource.objects.filter(mime_type='text/csv')
    for resource in resources:
        url = resource.file.url
        if url.endswith('.csv'):
            parts = list(os.path.split(url))
            if 'resources' not in parts:
                parts.insert(-1, 'resources')
            url = '/'.join(parts)
            resource.file = url
            resource.save()


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0004_add_ordering_for_resources'),
    ]

    operations = [
        migrations.RunPython(
            fix_imported_resource_urls, migrations.RunPython.noop),
    ]
