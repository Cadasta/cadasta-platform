# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
import math
from django.db import migrations, models


def make_org_names_unique(apps, schema_editor):
    Organization = apps.get_model('organization', 'Organization')
    names = {}
    max_length = Organization._meta.get_field('name').max_length
    for org in Organization.objects.all():
        orig_name = org.name
        for x in itertools.count(1):
            if not org.name in names:
                names[org.name] = True
                org.save()
                break
            name_length = max_length - int(math.log10(x)) - 2
            trunc_name = orig_name[:name_length]
            org.name = '{} {}'.format(trunc_name, x)

def make_project_names_unique(apps, schema_editor):
    Project = apps.get_model('organization', 'Project')
    names = {}
    max_length = Project._meta.get_field('name').max_length
    for project in Project.objects.all():
        if not project.organization in names:
            names[project.organization] = {}
        orig_name = project.name
        for x in itertools.count(1):
            if not project.name in names[project.organization]:
                names[project.organization][project.name] = True
                project.save()
                break
            name_length = max_length - int(math.log10(x)) - 2
            trunc_name = orig_name[:name_length]
            project.name = '{} {}'.format(trunc_name, x)


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [

        # Run database modifications to ensure that names are unique
        migrations.RunPython(
            make_org_names_unique,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            make_project_names_unique,
            reverse_code=migrations.RunPython.noop
        ),

        # Run actual database schema modifications
        migrations.AlterField(
            model_name='historicalorganization',
            name='name',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='project',
            unique_together=set([('organization', 'name')]),
        ),
    ]
