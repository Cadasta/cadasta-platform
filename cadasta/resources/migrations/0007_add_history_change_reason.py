# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-09 06:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0006_randomize_imported_filenames'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalcontentobject',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalresource',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
