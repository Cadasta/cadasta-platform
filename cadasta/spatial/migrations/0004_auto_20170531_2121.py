# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-31 21:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spatial', '0003_custom_location_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalspatialunit',
            name='area',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='spatialunit',
            name='area',
            field=models.FloatField(null=True),
        ),
    ]
