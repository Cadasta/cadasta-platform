from django.test import TestCase

from accounts.tests.factories import UserFactory

from ..fields import ProjectRoleField, PublicPrivateField


class ProjectRoleFieldTest(TestCase):
    def test_init(self):
        user = UserFactory.build()
        choices = (('Ab', 'Ahh Bee',),)
        field = ProjectRoleField(user, choices=choices)
        assert field.widget.user == user
        assert field.widget.choices == [choices[0]]


class PublicPrivateFieldTest(TestCase):
    def test_clean(self):
        field = PublicPrivateField()
        assert field.clean(None) == 'public'
        assert field.clean('on') == 'private'
