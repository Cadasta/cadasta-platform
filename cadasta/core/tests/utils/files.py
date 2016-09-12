import pytest
import shutil
import os

from django.conf import settings
from buckets.utils import ensure_dirs


@pytest.fixture(scope='class')
def make_dirs(request):
    ensure_dirs('uploads/resources', 'uploads/xls-forms', 'uploads/xml-forms',
                'downloads')

    def teardown():
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 's3'))
    request.addfinalizer(teardown)
