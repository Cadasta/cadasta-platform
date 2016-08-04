import os
from django.conf import settings
from buckets.test.storage import FakeS3Storage
path = os.path.dirname(settings.BASE_DIR)


def get_form(form_name):
    storage = FakeS3Storage()
    file = open(
        path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
        'rb'
    ).read()
    form = storage.save('xls-forms/{}.xlsx'.format(form_name), file)
    return form
