import os
from django.conf import settings
from buckets.test.storage import FakeS3Storage
from core.tests.factories import PolicyFactory
from jsonattrs.models import create_attribute_types


class UserTestCase:
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        create_attribute_types()


class FileStorageTestCase:
    def setUp(self):
        super().setUp()
        self.storage = FakeS3Storage()
        self.path = os.path.dirname(settings.BASE_DIR)

    def get_storage(self):
        return self.storage

    def get_file(self, path, mode):
        return open(self.path + path, mode)

    def get_form(self, form_name):
        file = self.get_file(
            path='/questionnaires/tests/files/{}.xlsx'.format(form_name),
            mode='rb')
        form = self.storage.save('xls-forms/{}.xlsx'.format(form_name),
                                 file.read())
        file.close()
        return form
