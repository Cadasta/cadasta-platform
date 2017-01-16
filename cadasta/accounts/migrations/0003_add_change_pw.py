# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-16 09:51
from __future__ import unicode_literals

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_activate_users_20161014_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='change_pw',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='change_pw',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='historicaluser',
            name='username',
            field=models.CharField(db_index=True, error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
    ]
