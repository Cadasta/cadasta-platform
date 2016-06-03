import os
from django.test import TestCase
from django.conf import settings
from buckets.test.utils import ensure_dirs
from buckets.test.storage import FakeS3Storage

from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from ..forms import ResourceForm, AddResourceFromLibraryForm
from .factories import ResourceFactory

path = os.path.dirname(settings.BASE_DIR)


class ResourceFormTest(TestCase):
    def setUp(self):
        ensure_dirs()
        storage = FakeS3Storage()
        file = open(path + '/resources/tests/files/image.jpg', 'rb')
        file_name = storage.save('image.jpg', file)

        self.data = {
            'name': 'Some name',
            'description': '',
            'file': file_name,
            'original_file': 'image.jpg'
        }
        self.project = ProjectFactory.create()

    def test_create_resource(self):
        user = UserFactory.create()
        form = ResourceForm(self.data,
                            content_object=self.project,
                            contributor=user,
                            project_id=self.project.id)
        assert form.is_valid() is True
        form.save()
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == self.data['name']
        assert self.project.resources.first().contributor == user

    def test_update_resource(self):
        user = UserFactory.create()
        resource = ResourceFactory(content_object=self.project,
                                   project=self.project)
        form = ResourceForm(self.data,
                            instance=resource,
                            contributor=user)
        assert form.is_valid() is True
        form.save()
        assert self.project.resources.count() == 1
        assert self.project.resources.first().name == self.data['name']
        assert self.project.resources.first().contributor == user


class AddResourceFromLibraryFormTest(TestCase):
    def test_init(self):
        prj = ProjectFactory.create()
        prj_res = ResourceFactory.create(project=prj, content_object=prj)
        res = ResourceFactory.create(project=prj)

        form = AddResourceFromLibraryForm(project_id=prj.id,
                                          content_object=prj)
        assert len(form.fields) == 2
        assert form.fields[prj_res.id].initial is True
        assert form.fields[res.id].initial is False

    def test_save(self):
        prj = ProjectFactory.create()
        prj_res = ResourceFactory.create(project=prj, content_object=prj)
        res = ResourceFactory.create(project=prj)

        data = {
            res.id: 'on'
        }

        form = AddResourceFromLibraryForm(data=data,
                                          project_id=prj.id,
                                          content_object=prj)

        assert form.is_valid() is True
        form.save()

        assert prj.resources.count() == 1
        assert res in prj.resources
        assert prj_res not in prj.resources
