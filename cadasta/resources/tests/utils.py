import pytest
import os
import shutil
from django.conf import settings


@pytest.fixture(scope='class')
def clear_temp(request):
    def teardown():
        path = os.path.join(settings.MEDIA_ROOT, 'temp')
        if os.path.exists(path):
            shutil.rmtree(path)
    request.addfinalizer(teardown)
