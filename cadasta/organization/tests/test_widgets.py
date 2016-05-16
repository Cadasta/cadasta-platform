from django.test import TestCase

from ..forms import FORM_CHOICES
from ..widgets import ProjectRoleWidget, PublicPrivateToggle

from accounts.tests.factories import UserFactory


class ProjectRoleWidgetTest(TestCase):
    def setUp(self):
        self.user = UserFactory.build(
            username='bob',
            email='me@example.com',
            full_name='Bob Smith'
        )
        self.widget = ProjectRoleWidget(user=self.user, choices=FORM_CHOICES)

    def test_render_with_admin(self):
        html = self.widget.render(self.user.username, 'A')

        expected = (
            '<tr>'
            '  <td>'
            '    <p>Bob Smith</p>'
            '    <p>bob</p>'
            '  </td>'
            '  <td>me@example.com</td>'
            '  <td>'
            '    Administrator'
            '  </td>'
            '</tr>'
        )
        assert expected == html

    def test_render_with_manager(self):
        html = self.widget.render(self.user.username, 'PM')

        expected = (
            '<tr>'
            '  <td>'
            '    <p>Bob Smith</p>'
            '    <p>bob</p>'
            '  </td>'
            '  <td>me@example.com</td>'
            '  <td>'
            '    <select name="bob">\n'
            '<option value="PU">Project User</option>\n'
            '<option value="DC">Data Collector</option>\n'
            '<option value="PM" selected="selected">Project Manager</option>\n'
            '<option value="Pb">Public User</option>\n'
            '</select>'
            '  </td>'
            '</tr>'
        )
        assert expected == html


class PublicPrivateToggleTest(TestCase):
    def test_render_public(self):
        widget = PublicPrivateToggle()
        html = widget.render('field-name', 'public')

        expected = (
            '<div class="public-private-widget">'
            '  <label for"field-name">Project visibility</label>'
            '  <div>'
            '    Public<br>'
            '    <span class="glyphicon glyphicon-eye-open"></span>'
            '  </div>'
            '  <div>'
            '    <input name="field-name"  type="checkbox"'
            '           data-toggle="toggle" data-onstyle="danger"'
            '           data-offstyle="success" data-on=" " data-off=" ">'
            '  </div>'
            '  <div>'
            '    Private<br>'
            '    <span class="glyphicon glyphicon-eye-close"></span>'
            '  </div>'
            '</div>'
        )

        assert expected == html

    def test_render_private(self):
        widget = PublicPrivateToggle()
        html = widget.render('field-name', 'private')

        expected = (
            '<div class="public-private-widget">'
            '  <label for"field-name">Project visibility</label>'
            '  <div>'
            '    Public<br>'
            '    <span class="glyphicon glyphicon-eye-open"></span>'
            '  </div>'
            '  <div>'
            '    <input name="field-name" checked type="checkbox"'
            '           data-toggle="toggle" data-onstyle="danger"'
            '           data-offstyle="success" data-on=" " data-off=" ">'
            '  </div>'
            '  <div>'
            '    Private<br>'
            '    <span class="glyphicon glyphicon-eye-close"></span>'
            '  </div>'
            '</div>'
        )

        assert expected == html
