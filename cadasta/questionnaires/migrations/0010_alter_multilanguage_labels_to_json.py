# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import ast
import json
from jsonattrs.models import Attribute
from django.db import migrations


def alter_multilanguage_labels_to_json(apps, schema_editor):
    for attr in Attribute.objects.all():
        label = attr.long_name
        try:
            dict_data = ast.literal_eval(label)
            attr.long_name = json.dumps(dict_data)
            attr.save()
        except:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0009_set_question_option_index_field_properties'),
    ]

    operations = [
        migrations.RunPython(
            alter_multilanguage_labels_to_json,
            reverse_code=migrations.RunPython.noop
        ),
    ]
