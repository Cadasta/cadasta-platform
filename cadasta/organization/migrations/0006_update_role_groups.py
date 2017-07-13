# -*- coding: utf-7 -*-
from __future__ import unicode_literals

from django.db import migrations


def update_org_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    oa = Group.objects.get(name='OrgAdmin')
    om = Group.objects.get(name='OrgMember')

    OrganizationRole = apps.get_model("organization", "OrganizationRole")
    for role in OrganizationRole.objects.all():
        role.group = oa if role.admin else om
        role.save(update_fields=['group'])


def update_project_roles(apps, schema_editor):

    groups = {
        'PM': 'ProjectManager',
        'DC': 'DataCollector',
        'PU': 'ProjectMember',
    }

    Group = apps.get_model("auth", "Group")
    ProjectRole = apps.get_model("organization", "ProjectRole")
    for project_role in ProjectRole.objects.all():
        project_role.group = Group.objects.get(name=groups[project_role.role])
        project_role.save(update_fields=['group'])


def update_public_user_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Group = apps.get_model("auth", "Group")
    PublicRole = apps.get_model("accounts", "PublicRole")
    pb_group = Group.objects.get(name="PublicUser")
    for user in User.objects.all():
        if not PublicRole.objects.filter(user=user).exists():
            PublicRole.objects.create(user=user, group=pb_group)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_groups'),
        ('organization', '0005_add_group_to_prj_org_roles'),
    ]

    operations = [
        migrations.RunPython(
            update_org_roles, migrations.RunPython.noop),
        migrations.RunPython(
            update_project_roles, migrations.RunPython.noop),
        migrations.RunPython(
            update_public_user_roles, migrations.RunPython.noop),
    ]
