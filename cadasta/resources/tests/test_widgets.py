from datetime import datetime
from django.test import TestCase
from django.template.defaultfilters import date

from core.tests.util import make_dirs  # noqa
from accounts.tests.factories import UserFactory
from .factories import ResourceFactory
from ..widgets import ResourceWidget


class ResourceWidgetTest(TestCase):
    def test_render(self):
        expected_html = (
            '  <td>'
            '    <img src="https://example.com/file-128x128.txt" '
            '         class="thumb-60">'
            '    <label for="file"><strong>Resource</strong></label>'
            '    <br>file.txt'
            '  </td>'
            '  <td class="hidden-xs hidden-sm">txt</td>'
            '  <td>0</td>'
            '  <td class="hidden-xs hidden-sm">'
            '      John Lennon<br>'
            '      john</td>'
            '  <td class="hidden-xs hidden-sm">{updated}</td>'
        )
        user = UserFactory.build(
            full_name='John Lennon',
            username='john'
        )
        last_updated = datetime.now()
        resource = ResourceFactory.build(
            name='Resource',
            file='https://example.com/file.txt',
            mime_type='image/png',
            contributor=user,
            last_updated=last_updated
        )
        widget = ResourceWidget(resource=resource)
        rendered = widget.render('file', True)
        assert expected_html.format(
            updated=date(last_updated, 'N j, Y, P')) in rendered
