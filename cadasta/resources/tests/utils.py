import pytest
import os
import shutil
from django.conf import settings


@pytest.fixture(scope='class')
def clear_temp(request):
    def teardown():
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'temp'))
    request.addfinalizer(teardown)
