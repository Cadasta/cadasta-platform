from datetime import datetime
from django.test import TestCase
from django.template.defaultfilters import date
from django.contrib.contenttypes.models import ContentType

from core.tests.utils.files import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from .factories import ResourceFactory
from ..models import ContentObject
from ..widgets import ResourceWidget


class ResourceWidgetTest(TestCase):
    def setUp(self):
        super().setUp()

        # Create a floating resource
        self.user = UserFactory.build(
            full_name='John Lennon',
            username='john'
        )
        self.last_updated = datetime.now()
        self.resource = ResourceFactory.build(
            name='Resource Name',
            file='https://example.com/file.txt',
            original_file='original_file.jpg',
            mime_type='image/png',
            contributor=self.user,
            last_updated=self.last_updated,
        )

        # Attach it to a project
        project = ProjectFactory.create()
        ContentObject.objects.create(
            resource=self.resource,
            content_type=ContentType.objects.get_for_model(project),
            object_id=project.id,
        )

    def test_render(self):
        expected_html = (
            '  <td>'
            '    <img src="https://example.com/file-128x128.txt"'
            '         class="thumb-60">'
            '    <label for="file"><strong>Resource Name</strong></label>'
            '    <br>original_file.jpg'
            '  </td>'
            '  <td class="hidden-xs hidden-sm">txt</td>'
            '  <td class="hidden-xs hidden-sm">'
            '      John Lennon<br>'
            '      john</td>'
            '  <td class="hidden-xs hidden-sm">{updated}</td>'
            '  <td>Attached to 1 other entity</td>'
        )
        widget = ResourceWidget(resource=self.resource)
        rendered = widget.render('file', True)
        assert expected_html.format(
            updated=date(self.last_updated, 'N j, Y, P'),
        ) in rendered

    def test_attachment_text_for_0_entities(self):
        widget = ResourceWidget(resource=self.resource)
        assert widget.get_attachment_text(0) == "Unattached"

    def test_attachment_text_for_1_entity(self):
        widget = ResourceWidget(resource=self.resource)
        assert widget.get_attachment_text(1) == (
            "Attached to 1 other entity")

    def test_attachment_text_for_more_entities(self):
        widget = ResourceWidget(resource=self.resource)
        for i in range(2, 11):
            assert widget.get_attachment_text(i) == (
                "Attached to {} other entities".format(i))
