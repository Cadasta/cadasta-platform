import os
from django.conf import settings


def ensure_dirs():
    path = os.path.join(settings.MEDIA_ROOT, 'temp')
    if not os.path.exists(path):
        os.makedirs(path)
