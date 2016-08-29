from datetime import datetime
from django.test import TestCase
from django.template.defaultfilters import date
from django.contrib.contenttypes.models import ContentType

from core.tests.util import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from .factories import ResourceFactory
from ..models import ContentObject
from ..widgets import ResourceWidget


class ResourceWidgetTest(TestCase):
    def base_test_render(self, num_entities, attachment_text):
        expected_html = (
            '  <td>'
            '    <img src="https://example.com/file-128x128.txt"'
            '         class="thumb-60">'
            '    <label for="file"><strong>Resource</strong></label>'
            '    <br>original_file.jpg'
            '  </td>'
            '  <td class="hidden-xs hidden-sm">txt</td>'
            '  <td class="hidden-xs hidden-sm">'
            '      John Lennon<br>'
            '      john</td>'
            '  <td class="hidden-xs hidden-sm">{updated}</td>'
            '  <td>{attachment_text}</td>'
        )
        user = UserFactory.build(
            full_name='John Lennon',
            username='john'
        )
        last_updated = datetime.now()
        resource = ResourceFactory.build(
            name='Resource',
            file='https://example.com/file.txt',
            original_file='original_file.jpg',
            mime_type='image/png',
            contributor=user,
            last_updated=last_updated,
        )
        if num_entities > 0:
            project = ProjectFactory.create()
            for i in range(num_entities):
                ContentObject.objects.create(
                    resource=resource,
                    content_type=ContentType.objects.get_for_model(project),
                    object_id=project.id,
                )
        widget = ResourceWidget(resource=resource)
        rendered = widget.render('file', True)
        assert expected_html.format(
            updated=date(last_updated, 'N j, Y, P'),
            attachment_text=attachment_text,
        ) in rendered

    def test_render_unattached_resource(self):
        self.base_test_render(0, "Unattached")

    def test_render_attached_resource_to_1_other(self):
        self.base_test_render(1, "Attached to 1 other entity")

    def test_render_attached_resource_to_2_other(self):
        self.base_test_render(2, "Attached to 2 other entities")

    def test_render_attached_resource_to_many_other(self):
        self.base_test_render(10, "Attached to 10 other entities")
