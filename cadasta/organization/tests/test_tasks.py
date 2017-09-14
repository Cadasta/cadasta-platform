from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from celery import Task

from accounts.tests.factories import UserFactory

from .factories import ProjectFactory
from ..tasks import schedule_project_export, export


class TaskTest(TestCase):

    def test_export_task(self):
        assert isinstance(export, Task)
        assert export.name == 'export.project'
        kwargs = {
            'org_slug': 'my-org',
            'project_slug': 'my-proj',
            'api_key': 'a-key',
            'output_type': 'all',
        }
        export(**kwargs)

    @patch('organization.tasks.TokenManager')
    @patch('organization.tasks.export')
    def test_schedule_project_export(self, export_task, token_mgr):
        proj = ProjectFactory.build(id='abcd')
        user = UserFactory.build(id=123)
        output_type = 'all'
        token_mgr.return_value.generate_token.return_value = 'fakeKey'

        schedule_project_export(proj, user, output_type)

        # Assert token generated
        token_mgr.assert_called_once_with(
            endpoints={'GET': [
                reverse(
                    'api:v1:organization:project_detail',
                    kwargs={
                        'organization': proj.organization.slug,
                        'project': proj.slug
                    }
                )]},
            max_age=43200,
            recipient='export-service',
            user=user,
        )
        token_mgr.return_value.generate_token.assert_called_once_with()

        # Assert task scheduled
        export_task.apply_async.assert_called_once_with(
            kwargs={
                'output_type': output_type,
                'org_slug': proj.organization.slug,
                'project_slug': proj.slug,
                'api_key': 'fakeKey',
            },
            creator_id=user.id,
            related_content_type_id=ContentType.objects.get_for_model(proj).id,
            related_object_id=proj.id,
        )
