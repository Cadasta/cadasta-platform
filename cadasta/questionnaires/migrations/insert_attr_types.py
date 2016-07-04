from django.db import migrations

from jsonattrs.models import create_attribute_type



class Migration(migrations.Migration):

    def insert_entity_attribute_types(apps, schema_editor):
        create_attribute_type('boolean', 'Boolean', 'BooleanField',
                              validator_type='bool',
                              validator_re=r'true|false|True|False')

        create_attribute_type('text', 'Text', 'CharField',
                              validator_type='str')
        create_attribute_type('text_multiline', 'Multiline text', 'CharField',
                              validator_type='str',
                              widget='Textarea')

        create_attribute_type('date', 'Date', 'DateField')
        create_attribute_type('dateTime', 'Date and time', 'DateTimeField')
        create_attribute_type('time', 'Time', 'TimeField')

        create_attribute_type('integer', 'Integer', 'IntegerField',
                              validator_re=r'[-+]?\d+')
        create_attribute_type('decimal', 'Decimal number', 'DecimalField',
                              validator_re=r'[-+]?\d+(\.\d+)?')

        create_attribute_type('email', 'Email address', 'EmailField')
        create_attribute_type('url', 'URL', 'URLField')

        create_attribute_type('select_one', 'Select one:', 'ChoiceField')
        create_attribute_type('select_multiple', 'Select multiple:',
                              'MultipleChoiceField')
        create_attribute_type('foreign_key', 'Select one:', 'ModelChoiceField')


    dependencies = [
        ('questionnaires', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_entity_attribute_types),
    ]
